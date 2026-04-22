###############################################################################
#  Copyright (C) 2024 LiveTalking@lipku https://github.com/lipku/LiveTalking
#  email: lipku@foxmail.com
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#       http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################
#
#  Avatar 基类 — 合并自 basereal.py，集成到 Async Pipeline
#

import math
from numpy.typing import NDArray
import torch
import numpy as np
import subprocess
import os
import time
import cv2
import glob
import resampy
import queue
from queue import Queue
from threading import Thread, Event
from io import BytesIO
import soundfile as sf
import asyncio
from enum import Enum
import json
import importlib
import registry

import torch.multiprocessing as mp
from dataclasses import dataclass, field

from av import AudioFrame, VideoFrame
from fractions import Fraction

from utils.logger import logger
from utils.image import read_imgs,mirror_index

# class State(Enum):
#     INIT=0
#     WAIT=1
#     QUESTION=2
#     ANSWER=3

@dataclass
class AudioFrameData:
    data: NDArray[np.float32]
    type: int = 0  # 默认值
    userdata: dict = field(default_factory=dict)

class BaseAvatar:
    def __init__(self, opt):
        self.opt = opt
        self.sample_rate = 16000
        self.chunk = self.sample_rate // (opt.fps*2) # 320 samples per chunk (20ms)
        self.sessionid = getattr(self.opt, 'sessionid', '0')

        self.speaking = False
        self.recording = False
        self.players = [] # Support multiple WebRTC connections
        self._record_video_pipe = None
        self._record_audio_pipe = None
        self.width = self.height = 0

        self.custom_audiotype = 0 # 0: normal, 1: sinlence, >1: custom audio
        self.custom_img_cycle = {}
        self.custom_audio_cycle = {}
        self.custom_audio_index = {}
        self.custom_index = {}
        # self.custom_opt = {}
        self.__loadcustom()

        self.batch_size = opt.batch_size
        self.res_frame_queue = Queue(self.batch_size*2)
        self.render_event = Event()

        _tts_modules = {
            'edgetts': 'tts.edge',
            'gpt-sovits': 'tts.sovits',
            'xtts': 'tts.xtts',
            'cosyvoice': 'tts.cosyvoice',
            'fishtts': 'tts.fish',
            'tencent': 'tts.tencent',
            'doubao': 'tts.doubao',
            'indextts2': 'tts.indextts2',
            'azuretts': 'tts.azure',
            'qwentts': 'tts.qwentts'
        }

        if opt.tts in _tts_modules:
            importlib.import_module(_tts_modules[opt.tts])
            self.tts = registry.create("tts", opt.tts, opt=opt, parent=self)
        else:
            logger.error(f"TTS module {opt.tts} not found.")

        _output_modules = {
            'webrtc': 'streamout.webrtc',
            'rtcpush': 'streamout.webrtc',
            'rtmp': 'streamout.rtmp',
            'virtualcam': 'streamout.virtualcam'
        }

        # 初始化 Output 模块
        if opt.transport in _output_modules:
            try:
                importlib.import_module(_output_modules[opt.transport])
                self.output = registry.create("streamout", opt.transport, opt=opt, parent=self)
            except ModuleNotFoundError:
                logger.error(f"Output transport module {_output_modules[opt.transport]} not found.")
        else:
            logger.error(f"Output transport {opt.transport} not found in map.")

    def add_player(self, player):
        if player in self.players:
            logger.info(f"Player already registered for session {self.sessionid}. Total: {len(self.players)}")
            return

        alive_players = []
        for existing in self.players:
            try:
                if getattr(existing.audio, 'readyState', None) == 'live' or getattr(existing.video, 'readyState', None) == 'live':
                    alive_players.append(existing)
            except Exception:
                pass
        self.players = alive_players

        if len(self.players) >= 2:
            old_p = self.players.pop(0)
            logger.warning(f"Ghost Buster: Pruning oldest stale connection from session {self.sessionid}")
            try:
                old_p.stop()
            except Exception:
                pass

        self.players.append(player)
        logger.info(f"Player added to session {self.sessionid}. Total: {len(self.players)}")

    def remove_player(self, player):
        if player in self.players:
            # Safely stop the individual player track without stopping the whole engine
            try:
                player.stop()
            except:
                pass
            self.players.remove(player)
            logger.info(f"Player removed from session {self.sessionid}. Remaining: {len(self.players)}")

    def push_video_all(self, frame):
        for p in self.players:
            try:
                p.push_video(frame)
            except Exception:
                pass # Prevent one slow player from crashing the engine

    def push_audio_all(self, frame, eventpoint=None):
        for p in self.players:
            try:
                p.push_audio(frame, eventpoint)
            except Exception:
                pass

    # 如果系统没有使用 pipeline，或者为了向后兼容原来的 ttsreal.py
    def put_msg_txt(self, msg, datainfo:dict={}):
        # 1. Flush FIRST before any new data is generated
        if hasattr(self, 'asr'):
            self.asr.flush_talk()
        
        while not self.res_frame_queue.empty():
            try: self.res_frame_queue.get_nowait()
            except: break

        # 2. THEN generate new data
        if hasattr(self, 'tts'):
            self.tts.put_msg_txt(msg, datainfo)
    
    def put_audio_frame(self, audio_chunk:NDArray[np.float32], datainfo:dict={}): # 16khz 20ms pcm
        if hasattr(self, 'asr'):
            self.speaking = True # Force speaking state
            # Force type 0 (Speech) for all TTS-generated audio
            audio_frame = AudioFrameData(type=0, data=audio_chunk, userdata=datainfo)
            self.asr.queue.put(audio_frame)

    def put_audio_file(self, filebyte, datainfo:dict={}): 
        input_stream = BytesIO(filebyte)
        stream = self.__create_bytes_stream(input_stream)
        streamlen = stream.shape[0]
        idx = 0
        first = True
        while streamlen >= self.chunk:
            eventpoint = {}
            if first:
                eventpoint = {'status': 'start'}
                first = False
            if streamlen - self.chunk < self.chunk:
                eventpoint = {'status': 'end'}
            eventpoint.update(**datainfo) 
            self.put_audio_frame(stream[idx:idx+self.chunk], eventpoint)
            streamlen -= self.chunk
            idx += self.chunk

    def put_audio_filepath(self, filepath, datainfo:dict={}): 
        stream = self.__create_bytes_stream(filepath)
        streamlen = stream.shape[0]
        idx = 0
        first = True
        while streamlen >= self.chunk:
            eventpoint = {}
            if first:
                eventpoint = {'status': 'start'}
                first = False
            if streamlen - self.chunk < self.chunk:
                eventpoint = {'status': 'end'}
            eventpoint.update(**datainfo) 
            self.put_audio_frame(stream[idx:idx+self.chunk], eventpoint)
            streamlen -= self.chunk
            idx += self.chunk
    
    def __create_bytes_stream(self, byte_stream):
        stream, sample_rate = sf.read(byte_stream) # [T*sample_rate,] float64
        logger.info(f'[INFO]put audio stream {sample_rate}: {stream.shape}')
        stream = stream.astype(np.float32)

        if stream.ndim > 1:
            logger.info(f'[WARN] audio has {stream.shape[1]} channels, only use the first.')
            stream = stream[:, 0]
    
        if sample_rate != self.sample_rate and stream.shape[0] > 0:
            logger.info(f'[WARN] audio sample rate is {sample_rate}, resampling into {self.sample_rate}.')
            stream = resampy.resample(x=stream, sr_orig=sample_rate, sr_new=self.sample_rate)

        return stream

    def flush_talk(self):
        if hasattr(self, 'tts') and hasattr(self.tts, 'flush_talk'):
            self.tts.flush_talk()
        if hasattr(self, 'asr') and hasattr(self.asr, 'flush_talk'):
            self.asr.flush_talk()
        self.custom_audiotype = 0  

    # def flush(self):
    #     self.flush_talk()

    def is_speaking(self) -> bool:
        return self.speaking
    
    def __loadcustom(self):
        if not hasattr(self.opt, 'customopt') or not self.opt.customopt:
            return
        for item in self.opt.customopt:
            logger.info(item)
            input_img_list = glob.glob(os.path.join(item['imgpath'], '*.[jpJP][pnPN]*[gG]'))
            input_img_list = sorted(input_img_list, key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
            self.custom_img_cycle[item['audiotype']] = read_imgs(input_img_list)
            if item.get('audiopath'):
                self.custom_audio_cycle[item['audiotype']], sample_rate = sf.read(item['audiopath'], dtype='float32')
                self.custom_audio_index[item['audiotype']] = 0
            self.custom_index[item['audiotype']] = 0
            # self.custom_opt[item['audiotype']] = item

    def init_customindex(self):
        self.custom_audiotype = 0
        for key in self.custom_audio_index:
            self.custom_audio_index[key] = 0
        for key in self.custom_index:
            self.custom_index[key] = 0

    def notify(self, eventpoint:dict):
        if eventpoint and eventpoint.get('status'):
            logger.info("notify:%s", eventpoint)

    def start_recording(self):
        if self.recording:
            return
        command = ['ffmpeg',
                    '-y', '-an',
                    '-f', 'rawvideo',
                    '-vcodec','rawvideo',
                    '-pix_fmt', 'bgr24',
                    '-s', "{}x{}".format(self.width, self.height),
                    '-r', str(25),
                    '-i', '-',
                    '-pix_fmt', 'yuv420p', 
                    '-vcodec', "h264",
                    f'temp{self.opt.sessionid}.mp4']
        self._record_video_pipe = subprocess.Popen(command, shell=False, stdin=subprocess.PIPE)

        acommand = ['ffmpeg',
                    '-y', '-vn',
                    '-f', 's16le',
                    '-ac', '1',
                    '-ar', '16000',
                    '-i', '-',
                    '-acodec', 'aac',
                    f'temp{self.opt.sessionid}.aac']
        self._record_audio_pipe = subprocess.Popen(acommand, shell=False, stdin=subprocess.PIPE)

        self.recording = True
    
    def record_video_data(self, image):
        if self.width == 0:
            self.height, self.width, _ = image.shape
        if self.recording:
            self._record_video_pipe.stdin.write(image.tostring())

    def record_audio_data(self, frame):
        if self.recording:
            self._record_audio_pipe.stdin.write(frame.tostring())
		
    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False 
        self._record_video_pipe.stdin.close()
        self._record_video_pipe.wait()
        self._record_audio_pipe.stdin.close()
        self._record_audio_pipe.wait()
        cmd_combine_audio = f"ffmpeg -y -i temp{self.opt.sessionid}.aac -i temp{self.opt.sessionid}.mp4 -c:v copy -c:a copy data/record.mp4"
        os.system(cmd_combine_audio)

    # def mirror_index(self, size, index):
    #     turn = index // size
    #     res = index % size
    #     if turn % 2 == 0:
    #         return res
    #     else:
    #         return size - res - 1 
    
    def get_custom_audio_stream(self, audiotype):
        idx = self.custom_audio_index[audiotype]
        stream = self.custom_audio_cycle[audiotype][idx:idx+self.chunk]
        self.custom_audio_index[audiotype] += self.chunk
        if self.custom_audio_index[audiotype] >= self.custom_audio_cycle[audiotype].shape[0]:
            self.custom_audiotype = 1
        return stream
    
    def set_custom_state(self, audiotype, reinit=True):
        print('set_custom_state:', audiotype)
        if self.custom_audio_index.get(audiotype) is None:
            return
        self.custom_audiotype = audiotype
        if reinit:
            self.custom_audio_index[audiotype] = 0
            self.custom_index[audiotype] = 0

    # ========================== 核心渲染及 Pipeline 桥接 ==========================
    def get_avatar_length(self):
        if hasattr(self, 'frame_list_cycle') and self.frame_list_cycle:
            return len(self.frame_list_cycle)
        return 0
        
    def inference(self, quit_event):
        length = self.get_avatar_length()
        index = 0
        count = 0
        counttime = 0
        last_speaking = False

        # syncnet_T = 12  # 时间步
        # weight_dtype = torch.float16  # 数据类型
        # infernum = 0
        logger.info('start inference')
        while not quit_event.is_set():
            # 1. Pull audio frames FIRST to maintain sync
            audio_frames: list[AudioFrameData] = []
            is_all_silence = True
            
            try:
                # Pull raw audio matching the batch size (2 chunks per frame)
                for _ in range(self.batch_size * 2):
                    audioframe: AudioFrameData = self.asr.output_queue.get(block=True, timeout=1)
                    if audioframe.type == 0:
                        is_all_silence = False
                    audio_frames.append(audioframe)
            except queue.Empty:
                continue

            current_speaking = not is_all_silence
            
            if is_all_silence:
                # Silence Mode: Standard background loop
                for i in range(self.batch_size):
                    self.res_frame_queue.put((None, audio_frames[i*2:i*2+2], mirror_index(length, index)))
                    index += 1
            else:
                # Speaking Mode: AI lipsync inference
                try:
                    audiofeat_batch = self.asr.feat_queue.get(block=True, timeout=0.2)
                    
                    if current_speaking and not last_speaking:
                        index = 0 # Reset for sync
                        
                    pred = self.inference_batch(index, audiofeat_batch)
                    
                    for i, res_frame in enumerate(pred):
                        try:
                            self.res_frame_queue.put((res_frame, audio_frames[i*2:i*2+2], mirror_index(length, index)), block=False)
                        except queue.Full:
                            # Drop oldest frame if queue full to prevent deadlock
                            try: self.res_frame_queue.get_nowait()
                            except: pass
                            self.res_frame_queue.put((res_frame, audio_frames[i*2:i*2+2], mirror_index(length, index)), block=False)
                        index += 1
                except queue.Empty:
                    # Fallback if features delayed
                    for i in range(self.batch_size):
                        try:
                            self.res_frame_queue.put((None, audio_frames[i*2:i*2+2], mirror_index(length, index)), block=False)
                        except queue.Full:
                            pass
                        index += 1
                    
            if current_speaking != last_speaking:
                logger.info(f"Speaking state shift: {'Silent' if last_speaking else 'Speaking'} -> {'Speaking' if current_speaking else 'Silent'}")
                last_speaking = current_speaking         
            
            # Diagnostic: Inference loop alive
            if index % 100 == 0:
                logger.debug(f"[DIAG] Inference Loop Active: frame_index={index}, speaking={current_speaking}")
        logger.info('baseavatar inference thread stop')

    def process_frames(self,quit_event):
        enable_transition = False  # 设置为False禁用过渡效果，True启用
        
        _last_speaking = False
        _transition_start = time.time()
        if enable_transition:
            _transition_duration = 0.1  # 过渡时间
            _last_silent_frame = None  # 静音帧缓存
            _last_speaking_frame = None  # 说话帧缓存

        # self.output.start() # No longer used
        _total_frames_pushed = 0
        _standby_frame = None
        
        while not quit_event.is_set():
            try:
                audio_frames: list[AudioFrameData]
                # Increase timeout if speaking to wait for processed frames
                timeout = 0.08 if self.speaking else 0.04
                res_frame,audio_frames,idx = self.res_frame_queue.get(block=True, timeout=timeout) 
                _last_idx = idx
            except queue.Empty:
                # Fast-Start: If queue is empty, push a standby background frame to keep stream alive
                if hasattr(self, 'frame_list_cycle') and self.frame_list_cycle:
                    # Use index 0 or last known index and INCREMENT it
                    idx = getattr(self, '_last_idx', 0)
                    target_frame = self.frame_list_cycle[mirror_index(len(self.frame_list_cycle), idx)]
                    self.push_video_all(target_frame)
                    
                    self._last_idx = (idx + 1) % len(self.frame_list_cycle)
                    _total_frames_pushed += 1
                    if _total_frames_pushed % 25 == 0:
                        logger.info(f"[HEARTBEAT] Engine live (STANDBY): {_total_frames_pushed} frames [Active Links: {len(self.players)}]")
                continue
            
            self._last_idx = idx
            current_speaking = not (audio_frames[0].type!=0 and audio_frames[1].type!=0)
            if current_speaking != _last_speaking:
                logger.info(f"Streaming Shift: {'Idle' if _last_speaking else 'Live'} -> {'Live' if current_speaking else 'Idle'}")
                _transition_start = time.time()
            _last_speaking = current_speaking

            if res_frame is None: 
                # Background frame
                self.speaking = False
                target_frame = self.frame_list_cycle[idx]
                combine_frame = target_frame
            else:
                # AI Lipsync frame
                self.speaking = True
                try:
                    combine_frame = self.paste_back_frame(res_frame,idx)
                except Exception as e:
                    logger.warning(f"Composite fail: {e}")
                    combine_frame = self.frame_list_cycle[idx]

            # Heartbeat Logging (every 25 frames = 1 second)
            _total_frames_pushed += 1
            if _total_frames_pushed % 25 == 0:
                status = "ACTIVE" if self.speaking else "STANDBY"
                links = len(self.players)
                logger.info(f"[HEARTBEAT] Engine live ({status}): {_total_frames_pushed} frames [Active Links: {links}]")

            # Push to ALL WebRTC relays
            self.push_video_all(combine_frame)
            self.record_video_data(combine_frame)

            for audio_frame in audio_frames:
                frame = (audio_frame.data * 32767).astype(np.int16)
                self.push_audio_all(frame, audio_frame.userdata)
                self.record_audio_data(frame)

        # NEVER stop the engine output loop for the persistent avatar
        # self.output.stop() 
        logger.info('baseavatar process_frames thread finished (STANDBY continues)') 

    def render(self,quit_event):
        self.quit_event = quit_event
        
        self.init_customindex()
        self.tts.render(quit_event)

        infer_quit_event = mp.Event()
        infer_thread = Thread(target=self.inference, args=(infer_quit_event,))
        infer_thread.start()
        
        process_quit_event = Event()
        process_thread = Thread(target=self.process_frames, args=(process_quit_event,))
        process_thread.start()

        count=0
        totaltime=0
        _starttime=time.perf_counter()
        _totalframe=0
        while not quit_event.is_set(): 
            t_start = time.perf_counter()
            self.asr.run_step()
            
            # Diagnostic: Main Render loop heartbeat
            _totalframe += self.batch_size
            if _totalframe % 100 == 0:
                logger.debug(f"[DIAG] Main Render Loop Active: processed_frames={_totalframe}")

            # Strict 25 FPS Throttle (40ms per step)
            # Each step pulls exactly batch_size video frames
            step_duration = (self.batch_size * 0.04) # 40ms per video frame
            
            elapsed = time.perf_counter() - t_start
            sleep_time = step_duration - elapsed
            
            # Dynamic buffer adjustment: if output queue is too full, slow down slightly
            # if too empty, speed up (but we are already in real-time)
            if sleep_time > 0:
                time.sleep(sleep_time)
        logger.info('baseavatar render thread stop')

        infer_quit_event.set()
        infer_thread.join()

        process_quit_event.set()
        process_thread.join()

