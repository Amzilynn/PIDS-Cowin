import os
import sys
import time
import asyncio
import base64
import cv2
import numpy as np
import socketio
import uvicorn
import tempfile
import struct
import edge_tts
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from avatar_engine import LivePortraitEngine
from audio_bridge import AudioLipSync, IdleAnimator

# =========================================================================
# CONFIGURATION
# =========================================================================
SOURCE_IMAGE = os.path.join(os.path.dirname(__file__), "ava.jpg")
DASHBOARD_FILE = os.path.join(os.path.dirname(__file__), "avatar_demo.html")
FPS = 6 # Hardware-locked floor for perfect timing
AUDIO_SYNC_OFFSET = 0.60 # Final tuned delay for 6 FPS
PORT = 8027

# =========================================================================
# GLOBAL STATE
# =========================================================================
app = FastAPI()
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
combined_app = socketio.ASGIApp(sio, app)

engine = None
lip_sync = AudioLipSync(sample_rate=16000)
idle_anim = IdleAnimator(fps=FPS)

is_speaking = False
speech_timeline = []
speech_start_time = 0

# =========================================================================
# CORE AVATAR LOOP
# =========================================================================
current_loop_task = None

async def idle_loop(sid):
    global is_speaking, current_loop_task
    print(f"[SYSTEM] Master Turbo Loop started for {sid}")
    frame_count = 0
    last_log_time = time.time()
    
    while True:
        try:
            if engine is None:
                await asyncio.sleep(0.1)
                continue
            
            if current_loop_task and asyncio.current_task() != current_loop_task:
                break
                
            t0 = time.time()
            
            # GET SYNC DATA
            lip_open = 0.0
            lip_spread = 0.0
            lip_pucker = 0.0
            
            if is_speaking and speech_timeline:
                # Apply AUDIO_SYNC_OFFSET to wait for browser audio to start
                elapsed_speech = time.time() - speech_start_time - AUDIO_SYNC_OFFSET
                
                if elapsed_speech >= 0:
                    frame_idx = int(elapsed_speech * FPS)
                    if frame_idx < len(speech_timeline):
                        sync_data = speech_timeline[frame_idx]
                        lip_open = sync_data["open"]
                        lip_spread = sync_data["spread"]
                        lip_pucker = sync_data["pucker"]
                    else:
                        is_speaking = False
                else:
                    # Still in the offset buffer, keep mouth closed
                    lip_open = 0.0
                    lip_spread = 0.0
                    lip_pucker = 0.0
            
            idle = idle_anim.get_idle_state()
            
            # RENDER
            frame = engine.render_frame(
                lip_open=lip_open, 
                lip_spread=lip_spread, 
                lip_pucker=lip_pucker,
                eye_blink=idle["eye_blink"], 
                head_tilt=idle["head_tilt"]
            )
            
            # ENCODE & EMIT
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_b64 = base64.b64encode(buffer).decode("utf-8")
            
            await sio.emit("avatar_frame", {"frame": frame_b64}, to=sid)
            
            # Heartbeat logging every 5 seconds
            frame_count += 1
            if time.time() - last_log_time > 5.0:
                print(f"[STREAM] Sent {frame_count} frames to {sid} | FPS: {frame_count / (time.time() - last_log_time):.1f}")
                frame_count = 0
                last_log_time = time.time()

            # Maintain stable FPS
            render_time = time.time() - t0
            wait_time = max(0, (1.0/FPS) - render_time)
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            print(f"[ERROR] Loop error: {e}")
            await asyncio.sleep(0.1)

# =========================================================================
# SPEECH PIPELINE
# =========================================================================
async def speak_pipeline(sid, text, voice):
    global is_speaking, speech_timeline, speech_start_time
    
    tmp_mp3 = os.path.join(tempfile.gettempdir(), "sarah_speech.mp3")
    tmp_wav = os.path.join(tempfile.gettempdir(), "sarah_speech.wav")
    
    try:
        # 0. Find local FFmpeg in the SHARED folder (which has the DLLs)
        ffmpeg_bin = os.path.join(os.path.dirname(__file__), "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffmpeg.exe")
        if not os.path.exists(ffmpeg_bin):
            # Try the root one as fallback
            ffmpeg_bin = os.path.join(os.path.dirname(__file__), "ffmpeg.exe")
            
        # 1. TTS Generation
        print(f"[TTS] Generating voice for: {text[:50]}...")
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tmp_mp3)
        
        # 2. Convert to PCM using LOCAL FFMPEG with DLL access
        # We run it from its own directory so it finds the DLLs
        ffmpeg_dir = os.path.dirname(ffmpeg_bin)
        res = os.system(f'cd /d "{ffmpeg_dir}" && ffmpeg.exe -y -i "{tmp_mp3}" -ar 16000 -ac 1 "{tmp_wav}" > nul 2>&1')
        
        # 3. Read PCM and Generate Timeline
        with open(tmp_wav, "rb") as f:
            pcm_bytes = f.read()
        n_samples = len(pcm_bytes) // 2
        pcm_data = np.array(struct.unpack(f"<{n_samples}h", pcm_bytes), dtype=np.float32) / 32768.0
        
        # USE OUR NEW PROFESSOR BRAIN
        speech_timeline = lip_sync.generate_timeline_smart(pcm_data, text, FPS)
        
        # 4. Stream audio to frontend (Broadcast to all connected)
        if os.path.exists(tmp_mp3) and os.path.getsize(tmp_mp3) > 0:
            with open(tmp_mp3, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode("utf-8")
            
            print(f"[CHAT] 👄 Sarah is broadcasting speech.")
            # Emit as 'avatar_audio' to match frontend listener
            await sio.emit("avatar_audio", {"audio": audio_b64, "text": text})
        else:
            print("[ERROR] ❌ TTS File is empty or missing.")
            return
        
        # 5. Start Sync Clock
        speech_start_time = time.time()
        is_speaking = True
        
    except Exception as e:
        print(f"[ERROR] ❌ Speech Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()

# =========================================================================
# API & SOCKETS
# =========================================================================
@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse(content="", status_code=204)

@app.get("/", response_class=HTMLResponse)
async def get_index():
    if os.path.exists(DASHBOARD_FILE):
        with open(DASHBOARD_FILE, "r") as f:
            return f.read()
    return "<h1>Sarah Avatar is Ready</h1>"

@app.post("/chat")
async def chat_endpoint(data: dict):
    text = data.get("text", "Hello")
    voice = data.get("voice", "en-US-AvaNeural")
    # Broadcast to everyone, no SID required!
    asyncio.create_task(speak_pipeline(None, text, voice))
    return {"status": "ok"}

@sio.on("connect")
async def connect(sid, environ):
    global current_loop_task
    print(f"[WS] Client {sid} connected.")
    current_loop_task = asyncio.create_task(idle_loop(sid))

@app.on_event("startup")
async def startup_event():
    global engine
    print("[SYSTEM] Sarah is waking up...")
    if os.path.exists(SOURCE_IMAGE):
        engine = LivePortraitEngine(SOURCE_IMAGE)
    
    print("[SYSTEM] Neural Link Engine ONLINE")

if __name__ == "__main__":
    print(f"[SYSTEM] Starting Uvicorn on port {PORT}...")
    uvicorn.run(combined_app, host="0.0.0.0", port=PORT)
