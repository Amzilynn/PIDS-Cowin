"""
Download MuseTalk Models Script
This script downloads all required model files for MuseTalk
"""
import os
import urllib.request
from huggingface_hub import hf_hub_download

def download_from_hf(repo_id, filename, local_dir):
    """Download a file from Hugging Face Hub"""
    print(f"\nDownloading {filename} from {repo_id}...")
    try:
        file_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=local_dir
        )
        print(f"✓ Downloaded to: {file_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(base_dir, "models")
    
    print("=" * 60)
    print("MuseTalk Model Downloader")
    print("=" * 60)
    
    # Check if huggingface_hub is installed
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("\n✗ huggingface_hub not installed. Installing...")
        os.system("pip install huggingface_hub")
        from huggingface_hub import hf_hub_download
    
    downloads = [
        {
            "name": "MuseTalk UNet config",
            "repo": "TMElyralab/MuseTalk",
            "filename": "musetalk.json",
            "local_dir": os.path.join(models_dir, "musetalk")
        },
        {
            "name": "MuseTalk UNet weights",
            "repo": "TMElyralab/MuseTalk",
            "filename": "pytorch_model.bin",
            "local_dir": os.path.join(models_dir, "musetalk")
        },
        {
            "name": "SD-VAE-FT-MSE config",
            "repo": "stabilityai/sd-vae-ft-mse",
            "filename": "config.json",
            "local_dir": os.path.join(models_dir, "sd-vae-ft-mse")
        },
        {
            "name": "SD-VAE-FT-MSE weights",
            "repo": "stabilityai/sd-vae-ft-mse",
            "filename": "diffusion_pytorch_model.bin",
            "local_dir": os.path.join(models_dir, "sd-vae-ft-mse")
        },
        {
            "name": "Whisper tiny model",
            "repo": "openai/whisper-tiny",
            "filename": "pytorch_model.bin",
            "local_dir": os.path.join(models_dir, "whisper")
        },
    ]
    
    success_count = 0
    for item in downloads:
        print(f"\n{'='*60}")
        print(f"Downloading: {item['name']}")
        print(f"{'='*60}")
        
        if download_from_hf(item["repo"], item["filename"], item["local_dir"]):
            success_count += 1
    
    # Download face-parse-bisent models manually (not on HF)
    print(f"\n{'='*60}")
    print("Downloading: Face Parse Bisent models")
    print(f"{'='*60}")
    
    face_parse_dir = os.path.join(models_dir, "face-parse-bisent")
    
    # ResNet18
    resnet_url = "https://download.pytorch.org/models/resnet18-5c106cde.pth"
    resnet_path = os.path.join(face_parse_dir, "resnet18-5c106cde.pth")
    print(f"\nDownloading ResNet18...")
    try:
        urllib.request.urlretrieve(resnet_url, resnet_path)
        print(f"✓ Downloaded ResNet18")
        success_count += 1
    except Exception as e:
        print(f"✗ Failed to download ResNet18: {e}")
    
    # You'll need to download 79999_iter.pth manually from:
    # https://drive.google.com/file/d/154JgKpzCPWn2q1fLzf6rLoz88n8sfB1l/view
    print(f"\n⚠ IMPORTANT: Download 79999_iter.pth manually from:")
    print(f"   https://drive.google.com/file/d/154JgKpzCPWn2q1fLzf6rLoz88n8sfB1l/view")
    print(f"   And place it in: {face_parse_dir}")
    
    print(f"\n{'='*60}")
    print(f"Download Summary: {success_count}/{len(downloads)+1} completed")
    print(f"{'='*60}")
    
    if success_count == len(downloads) + 1:
        print("\n✓ All models downloaded successfully!")
        print("\nNext steps:")
        print("1. Verify all files are in the models/ directory")
        print("2. Run: python avatars/musetalk/genavatar.py --file path/to/video.mp4 --avatar_id musetalk_avatar")
    else:
        print("\n⚠ Some downloads failed. Please check the errors above and retry.")

if __name__ == "__main__":
    main()
