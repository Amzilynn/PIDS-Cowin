import os
import sys
import json
import shutil
import torch
import cv2
import numpy as np
import soundfile as sf
import subprocess
import imageio_ffmpeg
import imageio
import uuid
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# ── Path Setup ─────────────────────────────────────────────────────────────
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from avatars.musetalk_avatar import load_model
from avatars.musetalk.utils.preprocessing import get_landmark_and_bbox
from utils.device import initialize_device

# ── Global Model Handles ────────────────────────────────────────────────────
gpu_device = initialize_device()
vae = None
unet = None
pe = None
timesteps = None
audio_processor = None

# ── Directory Constants ─────────────────────────────────────────────────────
DEFAULT_IMAGE  = os.path.join(project_root, "avalive.jpg")
OUTPUT_DIR     = os.path.join(os.path.dirname(project_root), "dso2", "frontend", "assets", "videos")
CHUNKS_DIR     = os.path.join(project_root, "temp_chunks")
AUDIO_SERVE    = os.path.join(project_root, "temp_audio_serve")
TEMP_AUDIO_DIR = os.path.join(project_root, "temp_musetalk", "data", "audio")

for d in [OUTPUT_DIR, CHUNKS_DIR, AUDIO_SERVE, TEMP_AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Performance Cache ───────────────────────────────────────────────────────
AVATAR_CACHE = {}

# ── Streaming Config ────────────────────────────────────────────────────────
CHUNK_FRAMES = 8    # Micro-chunks to drop time-to-first-video to < 7 seconds
BATCH_SIZE   = 8    # Safe batch memory execution 
SYNC_OFFSET  = -2   # Anticipatory lip-sync shift (-2 frames)


# ═══════════════════════════════════════════════════════════════════════════
#  Lifespan – Model Loading + torch.compile
# ═══════════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    global vae, unet, pe, timesteps, audio_processor

    print("[*] Loading VITAL Models into VRAM...")
    vae, unet, pe, timesteps, audio_processor = load_model()

    unet.model      = unet.model.to(device=gpu_device, dtype=torch.float16)
    vae.vae         = vae.vae.to(device=gpu_device, dtype=torch.float16)
    pe              = pe.to(device=gpu_device, dtype=torch.float16)
    timesteps       = timesteps.to(device=gpu_device)

    # ── Option 1: GPU Optimization ──────────────────────────────────────────
    # Note: torch.compile() is disabled here because Triton (the required 
    # compiler backend) is not officially supported or stable on Windows.
    # We rely on pure Float16 precision which yields a 5x speedup over PyTorch Windows BFloat16.
    print("[*] Eager Mode (Float16) active on RTX 5070.")

    print("[✓] All models ready for inference.")
    yield
    print("[*] Shutting down VITAL Avatar Service...")


# ═══════════════════════════════════════════════════════════════════════════
#  FastAPI App
# ═══════════════════════════════════════════════════════════════════════════
app = FastAPI(title="VITAL Avatar Service (Streaming)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve chunk files and audio files directly
app.mount("/stream-chunks", StaticFiles(directory=CHUNKS_DIR), name="stream-chunks")
app.mount("/audio",         StaticFiles(directory=AUDIO_SERVE), name="audio")


# ═══════════════════════════════════════════════════════════════════════════
#  Helper: Face Blending (Vectorised Numpy – no per-channel loop)
# ═══════════════════════════════════════════════════════════════════════════
def blend_face_image(background, ai_patch, face_coords, mask=None):
    px1, py1, px2, py2 = face_coords
    h_bg, w_bg = background.shape[:2]
    y_s, x_s = max(0, py1), max(0, px1)
    y_e, x_e = min(h_bg, py2), min(w_bg, px2)
    if (y_e - y_s) <= 0 or (x_e - x_s) <= 0:
        return background

    target_roi = background[y_s:y_e, x_s:x_e]
    ai_h, ai_w = ai_patch.shape[:2]
    roi_h, roi_w = y_e - y_s, x_e - x_s

    if ai_h != roi_h or ai_w != roi_w:
        ai_patch = cv2.resize(ai_patch, (roi_w, roi_h))

    if mask is None:
        mask = np.zeros((roi_h, roi_w), dtype=np.float32)
        cv2.rectangle(mask, (5, 5), (roi_w - 5, roi_h - 5), 1.0, -1)
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
    elif mask.shape[:2] != (roi_h, roi_w):
        mask = cv2.resize(mask, (roi_w, roi_h))

    # Colour-match brightness (LAB space)
    target_lab = cv2.cvtColor(target_roi, cv2.COLOR_BGR2LAB)
    ai_lab     = cv2.cvtColor(ai_patch,   cv2.COLOR_BGR2LAB)
    l_diff = int(np.mean(target_lab[:, :, 0]) - np.mean(ai_lab[:, :, 0]))
    ai_lab[:, :, 0] = np.clip(ai_lab[:, :, 0].astype(np.int16) + l_diff, 0, 255).astype(np.uint8)
    ai_patch = cv2.cvtColor(ai_lab, cv2.COLOR_LAB2BGR)

    # Vectorised blend (all channels at once)
    m3 = mask[:, :, np.newaxis]
    background[y_s:y_e, x_s:x_e] = (
        target_roi.astype(np.float32) * (1 - m3) +
        ai_patch.astype(np.float32)  * m3
    ).astype(np.uint8)

    return background


# ═══════════════════════════════════════════════════════════════════════════
#  Helper: Avatar Cache (landmarks + VAE latents)
# ═══════════════════════════════════════════════════════════════════════════
def _get_cached_avatar():
    if DEFAULT_IMAGE in AVATAR_CACHE:
        c = AVATAR_CACHE[DEFAULT_IMAGE]
        return c["img"].copy(), c["latents"], c["coords"]

    print("[*] First run – pre-processing avatar image (cached after this)...")
    img_orig = cv2.imread(DEFAULT_IMAGE)
    if img_orig is None:
        raise FileNotFoundError(f"Avatar image not found: {DEFAULT_IMAGE}")

    h_f, w_f = img_orig.shape[:2]
    w_f = w_f if w_f % 2 == 0 else w_f - 1
    h_f = h_f if h_f % 2 == 0 else h_f - 1
    img = img_orig[:h_f, :w_f]

    coords_list, _ = get_landmark_and_bbox([DEFAULT_IMAGE])
    if not coords_list or coords_list[0] == (0, 0, 0, 0):
        raise ValueError("Could not detect face landmarks in avatar image.")
    bx1, by1, bx2, by2 = coords_list[0]

    crop = cv2.resize(img[by1:by2, bx1:bx2], (256, 256))

    def prep(img_in, half_mask=False):
        t = cv2.cvtColor(img_in, cv2.COLOR_BGR2RGB).astype(np.float32)
        t = (t / 127.5) - 1.0
        if half_mask:
            t[t.shape[0] // 2:, :] = -1.0
        return torch.from_numpy(t).permute(2, 0, 1).unsqueeze(0).to(device=gpu_device, dtype=torch.bfloat16)

    with torch.no_grad():
        ref_lat    = vae.vae.encode(prep(crop)).latent_dist.mode() * vae.vae.config.scaling_factor
        masked_lat = vae.vae.encode(prep(crop, half_mask=True)).latent_dist.mode() * vae.vae.config.scaling_factor
        latents = torch.cat([masked_lat, ref_lat], dim=1)

    AVATAR_CACHE[DEFAULT_IMAGE] = {"img": img.copy(), "latents": latents, "coords": (bx1, by1, bx2, by2)}
    return img.copy(), latents, (bx1, by1, bx2, by2)


# ═══════════════════════════════════════════════════════════════════════════
#  Helper: Audio → Whisper Features
# ═══════════════════════════════════════════════════════════════════════════
def _process_audio(audio_path):
    audio_data, _ = sf.read(audio_path)
    if audio_data.ndim > 1:
        audio_data = audio_data.mean(axis=1)
    peak = np.abs(audio_data).max()
    if peak > 1e-6:
        audio_data = (audio_data / peak) * 0.8

    step = 20 * 16000
    feats = []
    for s in range(0, len(audio_data), step):
        end = min(s + step, len(audio_data))
        chunk = audio_data[s:end]
        pad = (30 * 16000) - len(chunk)
        if pad > 0:
            chunk = np.pad(chunk, (0, pad))
        f = audio_processor.audio2feat(chunk)
        actual = int(((end - s) / 16000) * 50)
        feats.append(f[:actual])

    whisper_feat = np.concatenate(feats, axis=0)
    total_frames = int(len(audio_data) / 16000 * 25)
    return whisper_feat, total_frames


# ═══════════════════════════════════════════════════════════════════════════
#  Helper: Write a list of BGR frames to a silent MP4 chunk
# ═══════════════════════════════════════════════════════════════════════════
def _write_chunk(frames, out_path):
    # Try GPU NVENC for near-instant encoding, fallback to CPU libx264
    try:
        w = imageio.get_writer(out_path, fps=25, codec="h264_nvenc",
                               pixelformat="yuv420p", ffmpeg_log_level="error")
    except Exception:
        w = imageio.get_writer(out_path, fps=25, codec="libx264",
                               pixelformat="yuv420p", ffmpeg_log_level="error")
    for bgr in frames:
        w.append_data(bgr[:, :, ::-1])
    w.close()


# ═══════════════════════════════════════════════════════════════════════════
#  Core: Progressive Streaming Render Worker  (Option 2)
# ═══════════════════════════════════════════════════════════════════════════
def render_worker_streaming(audio_path: str, output_filename: str, job_id: str):
    chunk_dir   = os.path.join(CHUNKS_DIR, job_id)
    os.makedirs(chunk_dir, exist_ok=True)
    status_path = os.path.join(chunk_dir, "manifest.json")

    # Copy audio so the frontend can play it in sync with the chunks
    audio_serve = os.path.join(AUDIO_SERVE, f"{job_id}.wav")
    shutil.copy(audio_path, audio_serve)

    manifest = {
        "job_id":       job_id,
        "status":       "rendering",
        "audio_url":    f"/audio/{job_id}.wav",
        "chunks":       [],
        "done":         False,
        "total_frames": 0,
        "final_url":    None,
    }

    def save():
        with open(status_path, "w") as f:
            json.dump(manifest, f)

    save()

    try:
        img, latents, (bx1, by1, bx2, by2) = _get_cached_avatar()
        whisper_feat, total_f = _process_audio(audio_path)

        manifest["total_frames"] = total_f
        save()

        # Pre-compute the lip-region mask once (same size every frame)
        face_mask = None
        frame_buffer = []
        chunk_idx    = 0

        print(f"[STREAM:{job_id[:8]}] Rendering {total_f} frames → chunks of {CHUNK_FRAMES}...")

        for i in range(0, total_f, BATCH_SIZE):
            bs = min(BATCH_SIZE, total_f - i)

            aud_chunks = []
            for j in range(bs):
                # Apply SYNC_OFFSET for better natural feel
                f_idx = max(0, i + j + SYNC_OFFSET)
                chunk, _ = audio_processor.get_sliced_feature(whisper_feat, f_idx, [2, 2], 25)
                # Ensure we handle various return types from audio_processor
                aud_chunks.append(chunk[0] if isinstance(chunk, (list, np.ndarray)) and len(chunk.shape) > 2 else chunk)

            aud_batch = torch.from_numpy(np.stack(aud_chunks)).to(device=gpu_device, dtype=torch.float16)
            aud_batch = pe(aud_batch)
            lat_batch = latents.repeat(bs, 1, 1, 1).to(dtype=torch.float16)

            with torch.no_grad():
                pred   = unet.model(lat_batch, timesteps, encoder_hidden_states=aud_batch).sample
                pred   = torch.nan_to_num(pred, nan=0.0)
                decoded = vae.decode_latents(pred)

            for j in range(bs):
                raw  = decoded[j].astype(np.uint8)
                h_p, w_p = raw.shape[:2]

                # Build face mask once
                if face_mask is None:
                    face_mask = np.zeros((h_p, w_p), dtype=np.float32)
                    cv2.rectangle(face_mask,
                                  (int(w_p * 0.1), int(h_p * 0.55)),
                                  (int(w_p * 0.9), int(h_p * 0.95)),
                                  1.0, -1)
                    face_mask = cv2.GaussianBlur(face_mask, (31, 31), 0)

                frame = blend_face_image(img.copy(), raw, [bx1, by1, bx2, by2],
                                         mask=face_mask.copy())
                frame_buffer.append(frame)

            # ── Flush a chunk whenever we have enough frames ───────────────
            while len(frame_buffer) >= CHUNK_FRAMES:
                chunk_frames = frame_buffer[:CHUNK_FRAMES]
                frame_buffer = frame_buffer[CHUNK_FRAMES:]

                fname = f"chunk_{chunk_idx:04d}.mp4"
                _write_chunk(chunk_frames, os.path.join(chunk_dir, fname))

                manifest["chunks"].append({
                    "index":  chunk_idx,
                    "url":    f"/stream-chunks/{job_id}/{fname}",
                    "frames": len(chunk_frames),
                })
                save()
                chunk_idx += 1
                print(f"[STREAM:{job_id[:8]}] ✓ Chunk {chunk_idx} ready  "
                      f"({i + bs}/{total_f} frames)")

        # ── Flush remaining frames as final chunk ──────────────────────────
        if frame_buffer:
            fname = f"chunk_{chunk_idx:04d}.mp4"
            _write_chunk(frame_buffer, os.path.join(chunk_dir, fname))
            manifest["chunks"].append({
                "index":  chunk_idx,
                "url":    f"/stream-chunks/{job_id}/{fname}",
                "frames": len(frame_buffer),
            })
            chunk_idx += 1

        # ── Merge all chunks + audio into the final single MP4 ─────────────
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        concat_txt  = os.path.join(chunk_dir, "concat.txt")
        merged_path = os.path.join(chunk_dir, "merged.mp4")
        final_path  = os.path.join(OUTPUT_DIR, output_filename)

        with open(concat_txt, "w") as f:
            for idx in range(chunk_idx):
                f.write(f"file '{os.path.join(chunk_dir, f'chunk_{idx:04d}.mp4')}'\n")

        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0",
                        "-i", concat_txt, "-c", "copy", merged_path],
                       capture_output=True)
        subprocess.run([ffmpeg, "-y", "-i", merged_path, "-i", audio_path,
                        "-c:v", "copy", "-c:a", "aac", "-shortest", final_path],
                       capture_output=True)

        manifest["done"]      = True
        manifest["status"]    = "complete"
        manifest["final_url"] = f"/assets/videos/{output_filename}"
        save()

        print(f"[STREAM:{job_id[:8]}] ✓ Full video written → {final_path}")

    except Exception as e:
        manifest["status"] = "error"
        manifest["error"]  = str(e)
        save()
        print(f"[STREAM ERROR:{job_id[:8]}] {e}")

    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


# ═══════════════════════════════════════════════════════════════════════════
#  Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {"status": "ok", "cache_keys": list(AVATAR_CACHE.keys())}


@app.post("/render/stream")
async def render_stream(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    filename: str = Form(None),
    job_id:   str = Form(None),
):
    """Start a progressive streaming render job. Returns manifest_url immediately."""
    if job_id is None:
        job_id = str(uuid.uuid4())
    audio_filename  = f"{job_id}.wav"
    video_filename  = filename if filename else f"{job_id}.mp4"
    audio_path      = os.path.join(TEMP_AUDIO_DIR, audio_filename)

    with open(audio_path, "wb") as f:
        f.write(await file.read())

    background_tasks.add_task(render_worker_streaming, audio_path, video_filename, job_id)

    return {
        "job_id":       job_id,
        "manifest_url": f"/stream/{job_id}/manifest",
        "video_url":    f"/assets/videos/{video_filename}",
    }


@app.get("/stream/{job_id}/manifest")
async def get_manifest(job_id: str):
    """Poll this to get available chunks and rendering status."""
    path = os.path.join(CHUNKS_DIR, job_id, "manifest.json")
    if not os.path.exists(path):
        return JSONResponse({
            "job_id": job_id, "status": "pending",
            "chunks": [], "done": False,
        })
    with open(path) as f:
        return JSONResponse(json.load(f))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
