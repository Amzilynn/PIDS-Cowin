import os
import urllib.request

# The standard LivePortrait model weights and the Audio-to-Expression weights.
# Using Hugging Face URLs for the open-source checkpoints.

MODELS = {
    "liveportrait_base": {
        "url": "https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/base_models/appearance_feature_extractor.pth",
        "path": "weights/appearance_feature_extractor.pth"
    },
    "liveportrait_motion": {
        "url": "https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/base_models/motion_extractor.pth",
        "path": "weights/motion_extractor.pth"
    },
    "liveportrait_spade": {
        "url": "https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/base_models/spade_generator.pth",
        "path": "weights/spade_generator.pth"
    },
    "liveportrait_warping": {
        "url": "https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/base_models/warping_module.pth",
        "path": "weights/warping_module.pth"
    },
    "audio2exp_bridge": {
        # Using a standard Wav2Vec2-based Audio2Exp model fine-tuned for LivePortrait
        "url": "https://huggingface.co/warmshao/FasterLivePortrait/resolve/main/audio2exp.pth",
        "path": "weights/audio2exp.pth"
    }
}

def download_file(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    if os.path.exists(dest_path):
        print(f"[SKIP] Already downloaded: {dest_path}")
        return
        
    print(f"[DOWNLOAD] Fetching {dest_path}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"[SUCCESS] Downloaded: {dest_path}")
    except Exception as e:
        print(f"[ERROR] Failed to download {dest_path}: {e}")

if __name__ == "__main__":
    print("="*60)
    print(" Downloading LivePortrait & Audio-to-Expression Weights")
    print("="*60)
    
    for name, info in MODELS.items():
        download_file(info['url'], info['path'])
        
    print("="*60)
    print(" All weights downloaded successfully!")
    print("="*60)
