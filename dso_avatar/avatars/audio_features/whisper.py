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
#  Whisper 音频特征提取 — 用于 MuseTalk
#  迁移自 museasr.py
#

import time
import numpy as np

import queue
from queue import Queue
from avatars.audio_features.base_asr import BaseASR
from avatars.musetalk.whisper.audio2feature import Audio2Feature
from threading import Thread
from utils.logger import logger

class WhisperASR(BaseASR):
    def __init__(self, opt, parent, audio_processor:Audio2Feature):
        super().__init__(opt, parent)
        self.audio_processor = audio_processor
        self.processing_queue = Queue()
        self.quit_event = parent.quit_event if hasattr(parent, 'quit_event') else None
        
        # Background thread for Whisper inference to prevent the render loop from stuttering
        self.worker_thread = Thread(target=self._processing_worker, daemon=True)
        self.worker_thread.start()
    
    def _processing_worker(self):
        """Background worker thread for Whisper inference."""
        local_frames = []
        while self.worker_thread.is_alive():
            try:
                # Retrieve from the lightweight feeder queue
                audio_batch = self.processing_queue.get(timeout=0.5)
                local_frames.extend(audio_batch)
                
                if len(local_frames) <= self.stride_left_size + self.stride_right_size:
                    continue

                # Prepare input data
                inputs = np.concatenate(local_frames)
                
                # Perform the heavy inference
                whisper_feature = self.audio_processor.audio2feat(inputs)
                whisper_chunks = self._feature2chunks(
                    feature_array=whisper_feature,
                    batch_size=self.batch_size,
                    audio_feat_win=[0,5],
                    start=self.stride_left_size/2,
                    feature_idx_multiplier=2
                )
                
                # Feed the inference batch queue
                self.feat_queue.put(whisper_chunks)
                
                # Maintain sliding window to minimize redundant processing
                local_frames = local_frames[-(self.stride_left_size + self.stride_right_size):]
                
            except queue.Empty:
                if self.quit_event and self.quit_event.is_set():
                    break
                continue
            except Exception as e:
                logger.error(f"Whisper background worker error: {e}")

    def _feature2chunks(self,feature_array,batch_size,audio_feat_win=[8,8],start=0,feature_idx_multiplier=1.0):
        feature_chunks = []
        for i in range(batch_size):
            selected_feature,selected_idx = self._get_sliced_feature(
                feature_array=feature_array, vid_idx=i+start,
                audio_feat_win=audio_feat_win, feature_idx_multiplier=feature_idx_multiplier)
            feature_chunks.append(selected_feature.reshape(-1, 384))
        return feature_chunks

    def run_step(self):
        ############################################## lightweight collector ##############################################
        batch_frames = []
        for _ in range(self.batch_size*2):
            audio_frame = self.get_audio_frame()
            batch_frames.append(audio_frame.data)
            self.output_queue.put(audio_frame)
        
        # Speedily hand off to the background thread
        self.processing_queue.put(batch_frames)
