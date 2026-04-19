"""
Download MuseTalk Models Script - UPDATED
Downloads all required model files for MuseTalk from official sources
"""
import os
import urllib.request
import subprocess
import sys

def download_file(url, destination, description):
    """Download a file with progress"""
    print(f"\n{'='*60}")
    print(f"Downloading: {description}")
    print(f"From: {url}")
    print(f"To: {destination}")
    print(f"{'='*60}")
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Download with urllib
        def reporthook(count, block_size, total_size):
            percent = int(count * block_size * 100 / total_size)
            downloaded = count * block_size / (1024 * 1024)
            total = total_size / (1024 * 1024)
            print(f"\rProgress: {percent}% ({downloaded:.1f}/{total:.1f} MB)", end='')
        
        urllib.request.urlretrieve(url, destination, reporthook)
        print(f"\n✓ Successfully downloaded: {description}")
        return True
    except Exception as e:
        print(f"\n✗ Failed to download {description}: {e}")
        return False

def download_with_hf_cli(repo_id, filename, local_dir, description):
    """Download using huggingface-cli if available"""
    print(f"\n{'='*60}")
    print(f"Downloading: {description}")
    print(f"{'='*60}")
    
    try:
        cmd = [
            sys.executable, "-m", "huggingface_cli",
            "download", repo_id,
            "--filename", filename,
            "--local-dir", local_dir
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Successfully downloaded: {description}")
            return True
        else:
            print(f"✗ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    
    print("="*60)
    print("MuseTalk Model Downloader - Official Models")
    print("="*60)
    print("\nThis will download ~2GB of model files.")
    print("Please ensure you have a stable internet connection.\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Download cancelled.")
        return
    
    downloads = [
        {
            "description": "MuseTalk UNet model (~1.5GB)",
            "url": "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk/pytorch_model.bin",
            "destination": os.path.join(models_dir, "musetalk", "pytorch_model.bin")
        },
        {
            "description": "MuseTalk UNet config",
            "url": "https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk/musetalk.json",
            "destination": os.path.join(models_dir, "musetalk", "musetalk.json")
        },
        {
            "description": "SD-VAE-FT-MSE weights (~335MB)",
            "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/diffusion_pytorch_model.bin",
            "destination": os.path.join(models_dir, "sd-vae-ft-mse", "diffusion_pytorch_model.bin")
        },
        {
            "description": "SD-VAE-FT-MSE config",
            "url": "https://huggingface.co/stabilityai/sd-vae-ft-mse/resolve/main/config.json",
            "destination": os.path.join(models_dir, "sd-vae-ft-mse", "config.json")
        },
        {
            "description": "Whisper tiny model (~150MB)",
            "url": "https://huggingface.co/openai/whisper-tiny/resolve/main/pytorch_model.bin",
            "destination": os.path.join(models_dir, "whisper", "tiny.pt")
        },
        {
            "description": "ResNet18 backbone (~45MB)",
            "url": "https://download.pytorch.org/models/resnet18-5c106cde.pth",
            "destination": os.path.join(models_dir, "face-parse-bisent", "resnet18-5c106cde.pth")
        },
    ]
    
    success_count = 0
    failed_downloads = []
    
    for item in downloads:
        if download_file(item["url"], item["destination"], item["description"]):
            success_count += 1
        else:
            failed_downloads.append(item["description"])
    
    # Manual download needed for these
    print(f"\n{'='*60}")
    print("MANUAL DOWNLOADS REQUIRED")
    print(f"{'='*60}")
    print("\nThe following files need manual download:")
    print("\n1. Face parsing model (79999_iter.pth):")
    print("   URL: https://drive.google.com/file/d/154JgKpzCPWn2q1fLzf6rLoz88n8sfB1l/view")
    print("   Save to:", os.path.join(models_dir, "face-parse-bisent", "79999_iter.pth"))
    
    print("\n2. DWPose model (dw-ll_ucoco_384.pth) - Only needed for avatar generation:")
    print("   URL: https://download.openmmlab.com/mmpose/v1/projects/rtmpose/dw-ll_ucoco_384.pth")
    print("   Save to:", os.path.join(models_dir, "dwpose", "dw-ll_ucoco_384.pth"))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"DOWNLOAD SUMMARY")
    print(f"{'='*60}")
    print(f"Successfully downloaded: {success_count}/{len(downloads)}")
    
    if failed_downloads:
        print(f"\nFailed downloads:")
        for item in failed_downloads:
            print(f"  - {item}")
    
    # Check what's actually present
    print(f"\n{'='*60}")
    print(f"CURRENT MODEL STATUS")
    print(f"{'='*60}")
    
    required_files = [
        os.path.join(models_dir, "musetalk", "pytorch_model.bin"),
        os.path.join(models_dir, "musetalk", "musetalk.json"),
        os.path.join(models_dir, "sd-vae-ft-mse", "diffusion_pytorch_model.bin"),
        os.path.join(models_dir, "sd-vae-ft-mse", "config.json"),
        os.path.join(models_dir, "whisper", "tiny.pt"),
        os.path.join(models_dir, "face-parse-bisent", "resnet18-5c106cde.pth"),
        os.path.join(models_dir, "face-parse-bisent", "79999_iter.pth"),
    ]
    
    all_present = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"{status} {file_path}")
        if not exists:
            all_present = False
    
    if all_present:
        print(f"\n{'='*60}")
        print("✓ ALL REQUIRED MODELS ARE PRESENT!")
        print(f"{'='*60}")
        print("\nNext steps:")
        print("1. Generate avatar from a reference video:")
        print("   python avatars/musetalk/genavatar.py --file path/to/video.mp4 --avatar_id musetalk_avatar")
        print("\n2. Run the application:")
        print("   python shared/main.py")
    else:
        print(f"\n{'='*60}")
        print("⚠ SOME MODELS ARE MISSING")
        print(f"{'='*60}")
        print("\nPlease download the missing files listed above.")
        print("The application will not work without all required models.")

if __name__ == "__main__":
    main()
