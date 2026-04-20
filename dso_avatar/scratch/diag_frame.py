import cv2
import numpy as np
import torch
import os
import sys
import pickle
from pathlib import Path

# Insert project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from avatars.musetalk_avatar import load_model, load_avatar
from utils.image import mirror_index

def debug_frame_dump(avatar_id="musetalk_avatar1"):
    print(f"[*] Starting Debug Frame Diagnostic for: {avatar_id}")
    
    # 1. Load Data
    frame_list, mask_list, coord_list, mask_coords_list, latent_list = load_avatar(avatar_id)
    vae, unet, pe, timesteps, audio_processor = load_model()
    
    # 2. Get a dummy audio feature (silence)
    audio_data = np.zeros(16000 * 2) # 2 seconds of silence
    whisper_feature = audio_processor.audio2feat(audio_data)
    chunk, _ = audio_processor.get_sliced_feature(whisper_feature, 0, [2,2], 25)
    
    # 3. Process Frame 0
    idx = 0
    latent = latent_list[idx].to(device=unet.device, dtype=unet.model.dtype)
    audio_feat = torch.from_numpy(chunk).unsqueeze(0).to(device=unet.device, dtype=unet.model.dtype)
    audio_feat = pe(audio_feat)
    
    with torch.no_grad():
        pred_latents = unet.model(latent, timesteps, encoder_hidden_states=audio_feat).sample
        pred = vae.decode_latents(pred_latents)[0]
    
    # 4. Diagnostics
    print(f"[*] AI Mouth Patch Mean: {np.mean(pred)}")
    print(f"[*] AI Mouth Patch Max: {np.max(pred)}")
    
    # 5. Save Parts
    cv2.imwrite("debug_ai_mouth.png", pred)
    cv2.imwrite("debug_orig_frame.png", frame_list[idx])
    cv2.imwrite("debug_mask.png", mask_list[idx])
    
    print("[!] Parts saved to disc. Check for white patches in debug_ai_mouth.png")

if __name__ == "__main__":
    debug_frame_dump()
