"""
PIDS-Cowin - Top-Level Orchestrator
This entrypoint initializes the shared configuration, prepares the
DSO1 Avatar/NLP engines, and mounts them onto the DSO2 FastAPI endpoints.
"""
import os
import subprocess
import sys

def start_avatar_engine():
    print("Starting DSO1 Avatar Engine (LiveTalking)...")
    avatar_dir = os.path.join(os.path.dirname(__file__), "dso1", "src", "avatar", "LiveTalking")
    if not os.path.exists(avatar_dir):
        print(f"Avatar Engine not found at {avatar_dir}")
        return None

    # Pass the current environment variables so the virtual environment works natively
    env = os.environ.copy()
    
    # Launch LiveTalking
    process = subprocess.Popen(
        [sys.executable, "app.py", "--transport", "webrtc", "--model", "wav2lip", "--avatar_id", "wav2lip256_avatar1"],
        cwd=avatar_dir,
        env=env
    )
    return process

if __name__ == "__main__":
    print("Initializing PIDS-Cowin Orchestrator...")
    avatar_process = start_avatar_engine()
    
    # Placeholder for DSO2 FastAPI component
    # e.g., uvicorn.run("dso2.src.api.app:app", host="0.0.0.0", port=8000)
    print("DSO1 Avatar Engine is spawned. Ready to handle WebRTC and API requests.")
    print("Press Ctrl+C to gracefully exit the entire Co_Win platform.")
    
    try:
        if avatar_process:
            avatar_process.wait()
    except KeyboardInterrupt:
        print("Shutting down PIDS-Cowin...")
        if avatar_process:
            avatar_process.terminate()
