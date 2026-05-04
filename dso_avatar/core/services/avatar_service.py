import os
import sys
import json
import copy
import shutil
import torch
import cv2
import numpy as np
import soundfile as sf
import subprocess
import imageio_ffmpeg
import imageio
import uuid
import resampy
import glob
import pickle
import time
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# ── Path Setup ─────────────────────────────────────────────────────────────
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from avatars.wav2lip import audio as wav2lip_audio
from avatars.wav2lip.models import Wav2Lip
from utils.device import initialize_device
from utils.image import mirror_index, read_imgs

# ── Helpers ───────────────────────────────────────────────────────────────
def load_wav2lip_model(path: str):
    if gpu_device == "cuda":
        checkpoint = torch.load(path)
    else:
        checkpoint = torch.load(path, map_location=lambda storage, loc: storage)
    s = checkpoint["state_dict"]
    new_s = {k.replace("module.", ""): v for k, v in s.items()}
    model = Wav2Lip()
    model.load_state_dict(new_s)
    return model.to(gpu_device).float().eval()

def load_wav2lip_avatar(avatar_id: str):
    avatar_path = os.path.join(project_root, "data", "avatars", avatar_id)
    full_imgs_path = os.path.join(avatar_path, "full_imgs")
    face_imgs_path = os.path.join(avatar_path, "face_imgs")
    coords_path    = os.path.join(avatar_path, "coords.pkl")

    with open(coords_path, "rb") as f:
        coord_list_cycle = pickle.load(f)

    input_img_list = sorted(glob.glob(os.path.join(full_imgs_path, "*.[jpJP][pnPN]*[gG]")),
                            key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    frame_list_cycle = read_imgs(input_img_list)

    input_face_list = sorted(glob.glob(os.path.join(face_imgs_path, "*.[jpJP][pnPN]*[gG]")),
                             key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
    face_list_cycle = read_imgs(input_face_list)

    return frame_list_cycle, face_list_cycle, coord_list_cycle

# ── Globals & Constants ───────────────────────────────────────────────────
gpu_device = initialize_device()
wav2lip_model = None
wav2lip_data = None

OUTPUT_DIR  = os.path.join(os.path.dirname(project_root), "dso2", "frontend", "assets", "videos")
CHUNKS_DIR  = os.path.join(project_root, "temp_chunks")
AUDIO_SERVE = os.path.join(project_root, "temp_audio_serve")
TEMP_DIR    = os.path.join(project_root, "temp_musetalk", "data", "audio")

for d in [OUTPUT_DIR, CHUNKS_DIR, AUDIO_SERVE, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

MEL_STEP_SIZE = 16
FPS           = 25
BATCH_SIZE    = 16
CHUNK_FRAMES  = 4

@asynccontextmanager
async def lifespan(app: FastAPI):
    global wav2lip_model, wav2lip_data
    print("[*] Loading Wav2Lip model...")
    wav2lip_model = load_wav2lip_model(os.path.join(project_root, "models", "wav2lip.pth"))
    print("[*] Loading sarah_static avatar data...")
    wav2lip_data = load_wav2lip_avatar("sarah_static")
    print("[✓] Wav2Lip ready.")
    yield

app = FastAPI(title="VITAL Avatar Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/stream-chunks", StaticFiles(directory=CHUNKS_DIR),  name="stream-chunks")
app.mount("/audio",         StaticFiles(directory=AUDIO_SERVE), name="audio")

# ── Core Logic ────────────────────────────────────────────────────────────

def audio_to_mel_chunks(audio_path: str):
    wav_path = audio_path
    if not audio_path.lower().endswith(".wav"):
        tmp_wav = os.path.join(TEMP_DIR, f"tmp_{uuid.uuid4()}.wav")
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", tmp_wav], capture_output=True)
        wav_path = tmp_wav
    
    audio_data, sr = sf.read(wav_path)
    if audio_data.ndim > 1: audio_data = audio_data.mean(axis=1)
    if sr != 16000: audio_data = resampy.resample(audio_data, sr, 16000)
    
    audio_data = audio_data.astype(np.float32)
    # Peak normalization for consistent mouth movement
    if np.max(np.abs(audio_data)) > 0:
        audio_data = audio_data / np.max(np.abs(audio_data))
        
    mel = wav2lip_audio.melspectrogram(audio_data)
    
    mel_idx_multiplier = 80.0 / FPS
    mel_chunks = []
    i = 0
    while True:
        start = int(i * mel_idx_multiplier)
        if start + MEL_STEP_SIZE > mel.shape[1]:
            mel_chunks.append(mel[:, mel.shape[1] - MEL_STEP_SIZE:])
            break
        mel_chunks.append(mel[:, start: start + MEL_STEP_SIZE])
        i += 1
    return mel_chunks

def _write_chunk(frames, out_path):
    """Writes a fragmented MP4 chunk for MSE compatibility."""
    h, w = frames[0].shape[:2]
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [
        ffmpeg, '-y',
        '-f', 'rawvideo', '-vcodec', 'rawvideo', '-s', f'{w}x{h}', '-pix_fmt', 'bgr24', '-r', str(FPS),
        '-i', '-',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-movflags', 'frag_keyframe+empty_moov+default_base_moof',
        '-f', 'mp4', out_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for f in frames:
        proc.stdin.write(f.tobytes())
    proc.stdin.close()
    proc.wait()

def render_worker_streaming(audio_path: str, output_filename: str, job_id: str):
    chunk_dir = os.path.join(CHUNKS_DIR, job_id)
    os.makedirs(chunk_dir, exist_ok=True)
    status_path = os.path.join(chunk_dir, "manifest.json")
    
    # Copy audio for frontend
    audio_serve = os.path.join(AUDIO_SERVE, f"{job_id}.wav")
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", audio_serve], capture_output=True)

    manifest = {
        "job_id": job_id, "status": "rendering", "audio_url": f"/audio/{job_id}.wav",
        "chunks": [], "done": False, "total_frames": 0, "final_url": None
    }
    def save():
        with open(status_path, "w") as f: json.dump(manifest, f)
    save()

    try:
        mel_chunks = audio_to_mel_chunks(audio_path)
        frame_list, face_list, coord_list = wav2lip_data
        num_avatar_frames = len(frame_list)
        total_f = len(mel_chunks)
        manifest["total_frames"] = total_f
        save()

        frame_buffer = []
        chunk_idx = 0

        for batch_start in range(0, total_f, BATCH_SIZE):
            bs = min(BATCH_SIZE, total_f - batch_start)
            
            img_batch = []
            for j in range(bs):
                idx = mirror_index(num_avatar_frames, batch_start + j)
                img_batch.append(face_list[idx])
            img_batch = np.asarray(img_batch, dtype=np.float32)

            mel_batch = np.asarray([mel_chunks[batch_start + j] for j in range(bs)])
            img_masked = img_batch.copy()
            img_masked[:, img_batch.shape[1] // 2:] = 0.0
            
            img_in = np.concatenate((img_masked, img_batch), axis=3) / 255.0
            mel_in = np.reshape(mel_batch, [bs, 80, MEL_STEP_SIZE, 1])
            
            # Wav2Lip expects RGB. img_in has 6 channels: [B_masked, G_masked, R_masked, B_orig, G_orig, R_orig]
            # We need to swap each 3-channel group separately.
            img_in_rgb = np.empty_like(img_in)
            img_in_rgb[:, :, :, 0:3] = img_in[:, :, :, 0:3][:, :, :, ::-1] # Masked BGR -> RGB
            img_in_rgb[:, :, :, 3:6] = img_in[:, :, :, 3:6][:, :, :, ::-1] # Original BGR -> RGB
            img_in_rgb = img_in_rgb.copy()
            
            img_tensor = torch.from_numpy(np.transpose(img_in_rgb, (0, 3, 1, 2))).to(gpu_device).float()
            mel_tensor = torch.from_numpy(np.transpose(mel_in, (0, 3, 1, 2)).copy()).to(gpu_device).float()

            with torch.no_grad():
                pred = wav2lip_model(mel_tensor, img_tensor)
            
            # Convert back to BGR for CV2
            pred_np = pred.float().cpu().numpy().transpose(0, 2, 3, 1)[:, :, :, ::-1] * 255.0

            # Diagnostic: check if the lips are actually different from the input
            if batch_start == 0:
                h_crop = img_batch.shape[1]
                diff = np.abs(pred_np[0, h_crop//2:] - img_batch[0, h_crop//2:]).mean()
                energy = np.mean(np.abs(mel_in))
                print(f"[*] Sync: Delta={diff:.2f} Energy={energy:.2f}")

            for j in range(bs):
                idx = mirror_index(num_avatar_frames, batch_start + j)
                y1, y2, x1, x2 = coord_list[idx]
                full_frame = copy.deepcopy(frame_list[idx])
                h, w = y2 - y1, x2 - x1
                
                pred_face = cv2.resize(pred_np[j].astype(np.float32), (w, h))
                
                # Subtle sharpening to counter upscaling blur
                kernel = np.array([[0, -0.2, 0], [-0.2, 1.8, -0.2], [0, -0.2, 0]])
                pred_face = cv2.filter2D(pred_face, -1, kernel)
                
                # Expanded Elliptical Mask for better movement range
                mask = np.zeros((h, w), dtype=np.float32)
                center = (w // 2, int(h * 0.72)) # Slightly higher center
                axes = (int(w * 0.45), int(h * 0.28)) # Wider and taller
                cv2.ellipse(mask, center, axes, 0, 0, 360, 1.0, -1)
                
                # Smooth feathering
                blur_size = max(7, int(w * 0.2))
                if blur_size % 2 == 0: blur_size += 1
                mask = cv2.GaussianBlur(mask, (blur_size, blur_size), 0)[:,:,np.newaxis]
                
                # Blend with original frame
                pasted = (pred_face * mask + full_frame[y1:y2, x1:x2] * (1.0-mask))
                full_frame[y1:y2, x1:x2] = np.clip(pasted, 0, 255).astype(np.uint8)
                frame_buffer.append(full_frame)

            while len(frame_buffer) >= CHUNK_FRAMES:
                c_frames = frame_buffer[:CHUNK_FRAMES]
                del frame_buffer[:CHUNK_FRAMES]
                fname = f"chunk_{chunk_idx:04d}.mp4"
                _write_chunk(c_frames, os.path.join(chunk_dir, fname))
                manifest["chunks"].append({"url": f"/stream-chunks/{job_id}/{fname}"})
                save()
                chunk_idx += 1
        
        if frame_buffer:
            fname = f"chunk_{chunk_idx:04d}.mp4"
            _write_chunk(frame_buffer, os.path.join(chunk_dir, fname))
            manifest["chunks"].append({"url": f"/stream-chunks/{job_id}/{fname}"})
            save()

        # Final merge
        final_filename = output_filename or f"{job_id}.mp4"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        concat_txt = os.path.join(chunk_dir, "concat.txt")
        with open(concat_txt, "w") as f:
            for i in range(chunk_idx + (1 if frame_buffer else 0)):
                f.write(f"file 'chunk_{i:04d}.mp4'\n")
        
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-i", audio_serve, 
                        "-c:v", "copy", "-c:a", "aac", "-shortest", final_path], capture_output=True)
        
        manifest["done"] = True
        manifest["status"] = "complete"
        manifest["final_url"] = f"/assets/videos/{final_filename}"
        save()
        print(f"[✓] Render complete: {final_filename}")

    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"[!] Render failed: {e}")
        with open(os.path.join(project_root, "render_errors.log"), "a") as f:
            f.write(f"\n--- {job_id} ---\n{err_msg}\n")
        manifest["status"] = "error"
        save()
    finally:
        if os.path.exists(audio_path): os.remove(audio_path)

# ── Endpoints ─────────────────────────────────────────────────────────────

@app.post("/render/stream")
async def render_stream(background_tasks: BackgroundTasks, file: UploadFile = File(...), filename: str = Form(None), job_id: str = Form(None)):
    jid = job_id or str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".wav"
    audio_path = os.path.join(TEMP_DIR, f"{jid}{ext}")
    with open(audio_path, "wb") as f: f.write(await file.read())
    background_tasks.add_task(render_worker_streaming, audio_path, filename, jid)
    return {"job_id": jid, "manifest_url": f"/stream/{jid}/manifest", "video_url": f"/assets/videos/{filename or jid+'.mp4'}"}

@app.get("/stream/{job_id}/manifest")
async def get_manifest(job_id: str):
    path = os.path.join(CHUNKS_DIR, job_id, "manifest.json")
    if not os.path.exists(path): return {"job_id": job_id, "status": "pending", "chunks": [], "done": False}
    with open(path) as f: return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
