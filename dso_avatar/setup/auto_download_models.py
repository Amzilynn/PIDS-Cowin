"""
Auto-download MuseTalk Models - No user input required
"""
import os
import urllib.request
import sys

def download_file(url, destination, description):
    """Download a file with progress"""
    print(f"\n{'='*60}")
    print(f"Downloading: {description}")
    print(f"{'='*60}")
    
    try:
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            downloaded = count * block_size / (1024 * 1024)
            total = total_size / (1024 * 1024)
            print(f"\rProgress: {percent}% ({downloaded:.1f}/{total:.1f} MB)", end='', flush=True)
        
        urllib.request.urlretrieve(url, destination, reporthook)
        print(f"\n✓ Successfully downloaded: {description}\n")
        return True
    except Exception as e:
        print(f"\n✗ Failed: {e}\n")
        return False

base_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(base_dir, "models")

downloads = [
    ("MuseTalk UNet (~1.5GB)", "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk/pytorch_model.bin", os.path.join(models_dir, "musetalk", "pytorch_model.bin")),
    ("MuseTalk config", "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk/musetalk.json", os.path.join(models_dir, "musetalk", "musetalk.json")),
    ("SD-VAE weights (~335MB)", "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.bin", os.path.join(models_dir, "sd-vae-ft-mse", "diffusion_pytorch_model.bin")),
    ("SD-VAE config", "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/config.json", os.path.join(models_dir, "sd-vae-ft-mse", "config.json")),
    ("Whisper tiny (~150MB)", "https://huggingface.co/openai/whisper-tiny/resolve/main/pytorch_model.bin", os.path.join(models_dir, "whisper", "tiny.pt")),
    ("ResNet18 (~45MB)", "https://download.pytorch.org/models/resnet18-5c106cde.pth", os.path.join(models_dir, "face-parse-bisent", "resnet18-5c106cde.pth")),
]

print("Starting MuseTalk model downloads...")
success = 0
for desc, url, dest in downloads:
    if download_file(url, dest, desc):
        success += 1

print(f"\n{'='*60}")
print(f"Downloaded: {success}/{len(downloads)}")
print(f"{'='*60}")

# Manual downloads needed
print("\nMANUAL DOWNLOADS NEEDED:")
print("1. Face parsing: https://drive.google.com/file/d/154JgKpzCPWn2q1fLzf6rLoz88n8sfB1l/view")
print("   Save to: models/face-parse-bisent/79999_iter.pth")
print("\n2. DWPose (optional): https://download.openmmlab.com/mmpose/v1/projects/rtmpose/dw-ll_ucoco_384.pth")
print("   Save to: models/dwpose/dw-ll_ucoco_384.pth")
