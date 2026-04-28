import sys
sys.path.append('.')
import argparse
import numpy as np
import torch
from avatars.wav2lip_avatar import LipReal, load_avatar, load_model

class Opt:
    def __init__(self):
        self.batch_size = 4
        self.fps = 25
        self.modelres = 256
        self.avatar_id = 'sarah_static'
        self.tts = 'edgetts'
        self.REF_FILE = 'zh-CN-YunxiaNeural'
        self.REF_TEXT = None
        self.TTS_SERVER = 'http://127.0.0.1:9880'
        self.transport = 'webrtc'
        self.l = 10
        self.r = 3
opt = Opt()

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = load_model('./models/wav2lip.pth')
avatar = load_avatar('sarah_static')
lip_real = LipReal(opt, model, avatar)

print("Running inference...")
feat = np.zeros((4, 80, 16))
res = lip_real.inference_batch(0, feat)
print("Inference success! Output shape:", res.shape)
