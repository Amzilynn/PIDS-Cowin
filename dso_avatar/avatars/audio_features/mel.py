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
#  Mel 频谱音频特征提取 — 用于 Wav2Lip
#  迁移自 lipasr.py
#

import time
import torch
import numpy as np
import queue
from queue import Queue

from avatars.audio_features.base_asr import BaseASR
from avatars.wav2lip import audio
from utils.logger import logger

class MelASR(BaseASR):
    def __init__(self, opt, parent):
        super().__init__(opt, parent)
        # Restore look-ahead delay to fix random lip flapping (Wav2Lip needs context)
        self.stride_left_size = 10
        self.stride_right_size = 10
        self.frames = []
        while not self.queue.empty():
            try: self.queue.get_nowait()
            except: break
        while not self.output_queue.empty():
            try: self.output_queue.get_nowait()
            except: break
        while not self.feat_queue.empty():
            try: self.feat_queue.get_nowait()
            except: break
        logger.info(f"ASR Flush: Queues cleared for session {getattr(self.opt, 'sessionid', '0')}")

    def run_step(self):
        ############################################## extract audio feature ##############################################
        # get a frame of audio
        # stride_left + batch_size*2 + stride_right
        needed_frames = self.batch_size * 2
        collected_frames = []
        has_speech = False
        for _ in range(needed_frames):
            audioframe = self.get_audio_frame()
            self.frames.append(audioframe.data)
            collected_frames.append(audioframe)
            # put to output queue for the process_frames thread
            self.output_queue.put(audioframe)
            if audioframe.type == 0:  # type 0 = real speech
                has_speech = True

        # context not enough, do not run network.
        if len(self.frames) < needed_frames:
            return

        # ── KEY FIX: Only extract mel features when real speech is present ──
        # If all frames are silence, flush stale feat_queue entries and skip.
        if not has_speech:
            # Drain stale silence features so speech features can slot in immediately
            while not self.feat_queue.empty():
                try:
                    self.feat_queue.get_nowait()
                except Exception:
                    break
            # discard old frames
            expected_len = self.stride_left_size + self.stride_right_size + needed_frames
            if len(self.frames) > expected_len:
                self.frames = self.frames[-expected_len:]
            return

        inputs = np.concatenate(self.frames)  # [N * chunk]
        mel = audio.melspectrogram(inputs)
        # cut off stride
        left = max(0, self.stride_left_size * 80 / 50)
        right = min(len(mel[0]), len(mel[0]) - self.stride_right_size * 80 / 50)
        mel_idx_multiplier = 80. / self.fps
        mel_step_size = 16
        i = 0
        mel_chunks = []
        while i < (len(self.frames) - self.stride_left_size - self.stride_right_size) / 2:
            start_idx = int(left + i * mel_idx_multiplier)
            if start_idx + mel_step_size > len(mel[0]):
                mel_chunks.append(mel[:, len(mel[0]) - mel_step_size:])
            else:
                mel_chunks.append(mel[:, start_idx: start_idx + mel_step_size])
            i += 1

        if mel_chunks:
            try:
                self.feat_queue.put_nowait(mel_chunks)
            except Exception:
                # Queue full — discard oldest stale entry then retry
                try:
                    self.feat_queue.get_nowait()
                except Exception:
                    pass
                try:
                    self.feat_queue.put_nowait(mel_chunks)
                except Exception:
                    pass

        # discard the old part to save memory
        expected_len = self.stride_left_size + self.stride_right_size + needed_frames
        if len(self.frames) > expected_len:
            self.frames = self.frames[-expected_len:]

        # Optional: Emergency purge if the input queue is getting dangerously long
        if self.queue.qsize() > 50:
            logger.warning(f"[DEBUG] Emergency audio purge: {self.queue.qsize()} frames in queue")
            self.get_audio_frame()
