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

from avatars.musetalk_avatar import load_model, load_avatar
from utils.device import initialize_device
from utils.image import mirror_index

# Global device initialization for RTX 5070
gpu_device = initialize_device()
torch.backends.cudnn.benchmark = True


def blend_face_hd(background, ai_patch, face_coords, mask=None):
    """
    Seamlessly blends the AI mouth patch into the original HD frame.
    Uses Lab-space luminance matching and optional alpha mask.
    """
    px1, py1, px2, py2 = face_coords
    h_bg, w_bg = background.shape[:2]

    # 1. Coordinate Clamping
    y_s = max(0, py1)
    x_s = max(0, px1)
    y_e = min(h_bg, py2)
    x_e = min(w_bg, px2)
    
    if (y_e - y_s) <= 0 or (x_e - x_s) <= 0:
        return background

    # Extract target ROI and corresponding AI patch ROI
    target_roi = background[y_s:y_e, x_s:x_e]
    ai_h, ai_w = ai_patch.shape[:2]
    
    # Ensure ai_patch matches the target ROI size if it was clipped
    if ai_h != (y_e - y_s) or ai_w != (x_e - x_s):
        ai_patch = ai_patch[y_s-py1:y_e-py1, x_s-px1:x_e-px1]

    # 2. Lighting Match (Lab-space)
    if target_roi.size > 0:
        target_lab = cv2.cvtColor(target_roi, cv2.COLOR_BGR2LAB)
        ai_lab = cv2.cvtColor(ai_patch, cv2.COLOR_BGR2LAB)
        
        # Mean luminance matching
        mean_l_target = np.mean(target_lab[:, :, 0])
        mean_l_ai = np.mean(ai_lab[:, :, 0])
        
        l_diff = int(mean_l_target - mean_l_ai)
        ai_lab[:, :, 0] = np.clip(ai_lab[:, :, 0].astype(np.int16) + l_diff, 0, 255).astype(np.uint8)
        ai_patch = cv2.cvtColor(ai_lab, cv2.COLOR_LAB2BGR)

    # Strong edge smoothing
    ai_patch = cv2.bilateralFilter(ai_patch, 9, 75, 75)
    
    # Histogram matching
    match_roi = background[y_s:y_e, x_s:x_e]
    if match_roi.size > 0:
        for c in range(3):
            src_hist, _ = np.histogram(match_roi[:,:,c], bins=256, range=(0,256))
            src_cdf = src_hist.cumsum()
            src_cdf = (src_cdf / src_cdf[-1]) * 255
            
            dst_hist, _ = np.histogram(ai_patch[:,:,c], bins=256, range=(0,256))
            dst_cdf = dst_hist.cumsum()
            dst_cdf = (dst_cdf / dst_cdf[-1]) * 255
            
            lut = np.interp(src_cdf, dst_cdf, np.arange(256))
            ai_patch[:,:,c] = cv2.LUT(ai_patch[:,:,c], lut.astype(np.uint8))
    
    # Additional blur
    ai_patch = cv2.GaussianBlur(ai_patch, (5, 5), 0)

    # 3. Soft-Edge Blending
    h, w = ai_patch.shape[:2]
    if mask is None:
        mask = np.zeros((h, w), dtype=np.float32)
        cv2.rectangle(mask, (5, 5), (w - 5, h - 5), 1.0, -1)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
    else:
        # Match mask to any clipping that happened to ai_patch
        if mask.shape[0] != h or mask.shape[1] != w:
            mask = mask[y_s-py1:y_e-py1, x_s-px1:x_e-px1]
    
    # Direct composite with soft alpha mask
    output = background.copy()
    roi = output[y_s:y_e, x_s:x_e].astype(np.float32)
    ai_patch = ai_patch.astype(np.float32)
    
    for c in range(3):
        roi[:, :, c] = roi[:, :, c] * (1 - mask) + ai_patch[:, :, c] * mask
        
    output[y_s:y_e, x_s:x_e] = roi.astype(np.uint8)
    return output


def run_hd_inference(audio_path, avatar_id, output_path, batch_size=8, limit=None):
    print(f"[*] Initializing Blackwell HD Engine for Avatar: {avatar_id}")
    
    # 1. Load Systems
    vae, unet, pe, timesteps, audio_processor = load_model()
    
    # RTX 5070 Stability: Switch to BFloat16 (Native Blackwell Format)
    print("[*] RTX 5070 Detected: Enabling BFloat16 Stability Mode.")
    unet.model = unet.model.to(device=gpu_device, dtype=torch.bfloat16)
    vae.vae = vae.vae.to(device=gpu_device, dtype=torch.bfloat16)
    pe = pe.to(device=gpu_device, dtype=torch.bfloat16)
    timesteps = timesteps.to(device=gpu_device)

    # 2. Load Data
    frames, masks, coords, mask_coords, latents = load_avatar(avatar_id)
    cycle_len = len(latents)

    # 3. Audio Pipeline
    audio_data, sr = sf.read(audio_path)
    if audio_data.ndim > 1:
        audio_data = audio_data.mean(axis=1)
    
    # Normalization to prevent VAE saturation
    peak = np.abs(audio_data).max()
    if peak > 0.7:
        audio_data = (audio_data / peak) * 0.7
    
    if sr != 16000:
        import resampy
        audio_data = resampy.resample(audio_data, sr, 16000)

    whisper_feat = audio_processor.audio2feat(audio_data)
    total_f = int(len(audio_data) / 16000 * 25)
    if limit:
        total_f = min(limit, total_f)
    print(f"[*] Processing {total_f} frames...")

    # 4. Main Inference Loop
    final_frames = []
    torch.cuda.empty_cache()
    gc.collect()

    print("[*] Warming up Blackwell GPU... Initial batch takes ~60s.")
    for i in tqdm(range(0, total_f, batch_size)):
        cur_bs = min(batch_size, total_f - i)
        
        # Audio & Latent Batching
        aud_chunks = []
        lat_chunks = []
        for j in range(cur_bs):
            idx = mirror_index(cycle_len, i + j)
            chunk, _ = audio_processor.get_sliced_feature(whisper_feat, i + j, [2, 2], 25)
            aud_chunks.append(chunk)
            lat_chunks.append(latents[idx])
            
        aud_batch = torch.from_numpy(np.stack(aud_chunks)).to(device=gpu_device, dtype=torch.bfloat16)
        lat_batch = torch.cat(lat_chunks, dim=0).to(device=gpu_device, dtype=torch.bfloat16)
        aud_batch = pe(aud_batch)

        # UNet + VAE
        with torch.no_grad():
            pred_lat = unet.model(lat_batch, timesteps, encoder_hidden_states=aud_batch).sample
            # NaN Protection for Blackwell driver stability during warm-up
            pred_lat = torch.nan_to_num(pred_lat, nan=0.0)
            pred_imgs = vae.decode_latents(pred_lat)

        # Post-Processing
        for j in range(cur_bs):
            idx = mirror_index(cycle_len, i + j)
            raw_patch = pred_imgs[j]
            ori_frame = frames[idx].copy()
            h_orig, w_orig = ori_frame.shape[:2]
            
            # Get mouth coordinates from the pre-processed data
            mx1, my1, mx2, my2 = coords[idx]
            mw, mh = mx2 - mx1, my2 - my1
            
            # 1. RECONSTRUCT FACE BOX from mouth box (Reverse of rebuild_coords.py logic)
            # mx = x + 0.15w => w = mw / 0.9
            # my = y + 0.65h => h = mh / 0.45
            fw = int(mw / 0.9)
            fh = int(mh / 0.45)
            fx1 = int(mx1 - fw * 0.15)
            fy1 = int(my1 - fh * 0.65)
            fx2 = fx1 + fw
            fy2 = fy1 + fh
            
            # 2. Coordinate Alignment: Rotate AI patch 90 CW to match vertical frame
            ai_face_vertical = cv2.rotate(raw_patch.astype(np.uint8), cv2.ROTATE_90_CLOCKWISE)
            ai_face_resize = cv2.resize(ai_face_vertical, (fx2 - fx1, fy2 - fy1))
            
            # 3. Create Mouth Mask (local to the face box)
            # This mask targets the mouth area specifically within the face patch
            mask = np.zeros((fy2 - fy1, fx2 - fx1), dtype=np.float32)
            # The mouth is located at [mx1-fx1, my1-fy1] inside the face box
            cv2.rectangle(mask, (mx1 - fx1, my1 - fy1), (mx2 - fx1, my2 - fy1), 1.0, -1)
            mask = cv2.GaussianBlur(mask, (25, 25), 0) # Smooth transition
            
            # Optional debug save on first frame
            if i == 0 and j == 0:
                cv2.imwrite("debug_ai_mouth.png", ai_face_resize)
                cv2.imwrite("debug_orig_frame.png", ori_frame)
            
            # 4. Blend into original frame using the face coordinates and mouth mask
            final_f = blend_face_hd(ori_frame, ai_face_resize, [fx1, fy1, fx2, fy2], mask=mask)
            final_frames.append(final_f)

        if (i // batch_size) % 10 == 0:
            torch.cuda.empty_cache()
            gc.collect()

    # 5. Final Merge
    print("[*] Stitching final video...")
    tmp_vid = str(Path("temp_v.mp4").absolute())
    tmp_aud = str(Path("temp_a.wav").absolute())
    out_abs = str(Path(output_path).absolute())
    
    # Truncate audio for perfect sync
    sf.write(tmp_aud, audio_data[:int(len(final_frames) / 25 * 16000)], 16000)
    
    h_f, w_f = final_frames[0].shape[:2]
    vw = cv2.VideoWriter(tmp_vid, cv2.VideoWriter_fourcc(*'mp4v'), 25, (w_f, h_f))
    for f in final_frames:
        vw.write(f)
    vw.release()
    
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, '-y', '-i', tmp_vid, '-i', tmp_aud, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', out_abs], capture_output=True)
    
    if os.path.exists(tmp_vid): os.remove(tmp_vid)
    if os.path.exists(tmp_aud): os.remove(tmp_aud)
    print(f"[!] SUCCESS! Result saved to: {output_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--audio", type=str, required=True)
    p.add_argument("--avatar_id", type=str, default="musetalk_avatar1")
    p.add_argument("--output", type=str, default="hd_output.mp4")
    p.add_argument("--batch_size", type=int, default=8)
    p.add_argument("--limit", type=int, default=None)
    a = p.parse_args()
    
    run_hd_inference(a.audio, a.avatar_id, a.output, a.batch_size, a.limit)
