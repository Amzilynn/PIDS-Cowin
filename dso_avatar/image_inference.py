import argparse
import os
import cv2
import numpy as np
import torch
import soundfile as sf
import subprocess
import imageio_ffmpeg
import gc
import sys
from tqdm import tqdm
from pathlib import Path

# Ensure absolute paths for local imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from avatars.musetalk_avatar import load_model
from avatars.musetalk.utils.preprocessing import get_landmark_and_bbox
from utils.device import initialize_device

# Global device initialization for RTX 5070
gpu_device = initialize_device()
torch.backends.cudnn.benchmark = True

def blend_face_image(background, ai_patch, face_coords, mask=None):
    """
    Seamlessly blends the AI mouth patch into the original image.
    """
    px1, py1, px2, py2 = face_coords
    h_bg, w_bg = background.shape[:2]

    y_s, x_s = max(0, py1), max(0, px1)
    y_e, x_e = min(h_bg, py2), min(w_bg, px2)
    
    if (y_e - y_s) <= 0 or (x_e - x_s) <= 0:
        return background

    target_roi = background[y_s:y_e, x_s:x_e]
    ai_h, ai_w = ai_patch.shape[:2]
    
    if ai_h != (y_e - y_s) or ai_w != (x_e - x_s):
        ai_patch = cv2.resize(ai_patch, (x_e - x_s, y_e - y_s))
        if mask is not None:
            mask = cv2.resize(mask, (x_e - x_s, y_e - y_s))
            
    # Lighting Match (Lab-space)
    target_lab = cv2.cvtColor(target_roi, cv2.COLOR_BGR2LAB)
    ai_lab = cv2.cvtColor(ai_patch, cv2.COLOR_BGR2LAB)
    mean_l_target = np.mean(target_lab[:, :, 0])
    mean_l_ai = np.mean(ai_lab[:, :, 0])
    l_diff = int(mean_l_target - mean_l_ai)
    ai_lab[:, :, 0] = np.clip(ai_lab[:, :, 0].astype(np.int16) + l_diff, 0, 255).astype(np.uint8)
    ai_patch = cv2.cvtColor(ai_lab, cv2.COLOR_LAB2BGR)

    # Optimized Vectorized Blending (Numpy speedup)
    mask_3d = mask[:, :, np.newaxis]
    background[y_s:y_e, x_s:x_e] = (target_roi.astype(np.float32) * (1 - mask_3d) + ai_patch.astype(np.float32) * mask_3d).astype(np.uint8)
    return background

def run_image_inference(image_path, audio_path, output_path, batch_size=8, limit=None):
    print(f"[*] Initializing Blackwell Image Mode for: {image_path}")
    
    # 1. Load Systems
    vae, unet, pe, timesteps, audio_processor = load_model()
    print("[*] RTX 5070 Detected: Enabling BFloat16 Stability Mode.")
    unet.model = unet.model.to(device=gpu_device, dtype=torch.bfloat16)
    vae.vae = vae.vae.to(device=gpu_device, dtype=torch.bfloat16)
    pe = pe.to(device=gpu_device, dtype=torch.bfloat16)
    timesteps = timesteps.to(device=gpu_device)

    # 2. Process Image (Explicitly handling Vertical Orientation)
    print("[*] Processing Image Landmarks...")
    img = cv2.imread(image_path)
    if img is None:
        print(f"[!] Error: Could not read {image_path}")
        return
    
    h_orig, w_orig = img.shape[:2]
    print(f"[*] Image Dimensions: {w_orig}x{h_orig}")

    coords_list, frames = get_landmark_and_bbox([image_path])
    if not coords_list or coords_list[0] == (0,0,0,0):
        print("[!] Error: No face detected. Try a clearer portrait photo.")
        return
    
    bx1, by1, bx2, by2 = coords_list[0]
    # SAVE DEBUG CROP: This is what the AI will see
    crop_debug = img[by1:by2, bx1:bx2].copy()
    cv2.imwrite("DEBUG_FACE_INPUT.png", crop_debug)
    print(f"[*] Check 'DEBUG_FACE_INPUT.png' - if it's not a face, alignment failed.")

    resized_crop = cv2.resize(crop_debug, (256, 256), interpolation=cv2.INTER_LANCZOS4)
    
    # Encode Latents
    def prep_img(img_in, half_mask=False):
        # Normalize to [-1, 1] range (REQUIRED by MuseTalk VAE)
        img_in = cv2.cvtColor(img_in, cv2.COLOR_BGR2RGB).astype(np.float32)
        img_in = (img_in / 127.5) - 1.0
        if half_mask: 
            img_in[img_in.shape[0]//2:, :] = -1.0
        return torch.from_numpy(img_in).permute(2, 0, 1).unsqueeze(0).to(device=gpu_device, dtype=torch.bfloat16)

    with torch.no_grad():
        t_img = prep_img(resized_crop, half_mask=False)
        t_mask = prep_img(resized_crop, half_mask=True)
        ref_lat = vae.vae.encode(t_img).latent_dist.mode() * vae.vae.config.scaling_factor
        masked_lat = vae.vae.encode(t_mask).latent_dist.mode() * vae.vae.config.scaling_factor
        latents = torch.cat([masked_lat, ref_lat], dim=1)

    # 3. Audio Pipeline (Segmented for Unlimited Length)
    audio_data, sr = sf.read(audio_path)
    if audio_data.ndim > 1: audio_data = audio_data.mean(axis=1)
    
    # NORMALIZATION: Force audio peak to 0.7 to ensure the AI "hears" it
    peak = np.abs(audio_data).max()
    if peak > 1e-6:
        audio_data = (audio_data / peak) * 0.7
        print(f"[*] Audio Normalized (Peak was {peak:.4f})")
    else:
        print("[!] WARNING: Audio seems to be silent!")

    if sr != 16000:
        import resampy
        audio_data = resampy.resample(audio_data, sr, 16000).astype(np.float32)
        
    # SLIDING WINDOW: Process in 20s chunks to bypass Whisper's 30s "Wall"
    print("[*] Processing long audio features...")
    step = 20 * 16000 # 20 second blocks
    whisper_feats = []
    
    for start in range(0, len(audio_data), step):
        end = min(start + step, len(audio_data))
        chunk = audio_data[start:end]
        
        # Pad to exactly 30s to keep Whisper internal shapes happy
        pad_needed = (30 * 16000) - len(chunk)
        if pad_needed > 0:
            chunk = np.pad(chunk, (0, pad_needed))
            
        f = audio_processor.audio2feat(chunk)
        
        # Pull only the "real" tokens for this segment (50 tokens per second)
        actual_len = int(((end - start) / 16000) * 50)
        whisper_feats.append(f[:actual_len])
        
    whisper_feat = np.concatenate(whisper_feats, axis=0)
    print(f"[*] Total Audio Sync Track: {whisper_feat.shape} | Mean: {np.mean(whisper_feat):.4f}")
    
    total_f = int(len(audio_data) / 16000 * 25)
    if limit: total_f = min(limit, total_f)

    # 4. Main Inference (Professional FFmpeg Pipe Mode)
    print(f"[*] Generating {total_f} frames...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    tmp_vid = "temp_v.mp4"
    h_f, w_f = img.shape[:2]
    
    # CRITICAL: Even dimensions check
    w_f = w_f if w_f % 2 == 0 else w_f - 1
    h_f = h_f if h_f % 2 == 0 else h_f - 1
    img = img[:h_f, :w_f]
    
    # Initialize imageio writer with stable software encoding
    import imageio
    # libx264 is more compatible than nvenc on some Windows systems
    writer = imageio.get_writer(tmp_vid, fps=25, codec='libx264', pixelformat='yuv420p', ffmpeg_log_level='error')

    try:
        for i in tqdm(range(0, total_f, batch_size), desc="[*] Generating video"):
            cur_bs = min(batch_size, total_f - i)
            aud_chunks = []
            for j in range(cur_bs):
                # Using 5 frames of context (2 before, 2 after) for each frame
                chunk, _ = audio_processor.get_sliced_feature(whisper_feat, i + j, [2, 2], 25)
                aud_chunks.append(chunk)

            aud_batch = torch.from_numpy(np.stack(aud_chunks)).to(device=gpu_device, dtype=torch.bfloat16)
            aud_batch = pe(aud_batch)
            lat_batch = latents.repeat(cur_bs, 1, 1, 1)

            with torch.no_grad():
                pred_sample = unet.model(lat_batch, timesteps, encoder_hidden_states=aud_batch).sample
                pred_lat = torch.nan_to_num(pred_sample, nan=0.0)
                pred_imgs = vae.decode_latents(pred_lat)

            for j in range(cur_bs):
                raw_patch = pred_imgs[j].astype(np.uint8)
                h_p, w_p = raw_patch.shape[:2]
                mask = np.zeros((h_p, w_p), dtype=np.float32)
                cv2.rectangle(mask, (int(w_p*0.1), int(h_p*0.55)), (int(w_p*0.9), int(h_p*0.95)), 1.0, -1)
                mask = cv2.GaussianBlur(mask, (31, 31), 0)

                final_f = blend_face_image(img, raw_patch, [bx1, by1, bx2, by2], mask=mask)
                # Write directly via imageio (handles encoding internally)
                writer.append_data(final_f[:, :, ::-1])  # BGR to RGB
    finally:
        writer.close()

    # 5. Final Merge (Removed -shortest to ensure full length)
    print(f"[*] Merging Final High-Quality Result...")
    subprocess.run([
        ffmpeg_exe, '-y', 
        '-i', tmp_vid, 
        '-i', audio_path, 
        '-c:v', 'copy', # Copy stream for zero quality loss
        '-c:a', 'aac', 
        output_path
    ], capture_output=True)
    
    if os.path.exists(tmp_vid): 
        os.remove(tmp_vid)
    print(f"[!] SUCCESS! Result saved to: {output_path}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--image", type=str, required=True)
    p.add_argument("--audio", type=str, required=True)
    p.add_argument("--output", type=str, default="image_result.mp4")
    p.add_argument("--limit", type=int, default=None)
    a = p.parse_args()
    run_image_inference(a.image, a.audio, a.output, limit=a.limit)
