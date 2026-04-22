import torch
import warnings
import os
import sys

def initialize_device():
    # Inject FFmpeg path logic for Windows
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        if ffmpeg_dir not in os.environ["PATH"]:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
            print(f"[INFO] Injected FFmpeg path: {ffmpeg_dir}")
    except ImportError:
        print("[WARN] imageio_ffmpeg not found. Ensure FFmpeg is in your PATH.")

    if torch.cuda.is_available():
        return torch.device('cuda')
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device('mps')
    else:
        return torch.device('cpu')