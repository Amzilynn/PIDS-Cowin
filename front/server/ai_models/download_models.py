import os
from huggingface_hub import snapshot_download

def download_models_locally():
    print("="*60)
    print("AVALIVE MODEL DOWNLOADER")
    print("="*60)
    
    # Delegate Models (BioMistral + Whisper)
    delegate_dir = os.path.join(os.getcwd(), "delegate_models")
    os.makedirs(delegate_dir, exist_ok=True)
    
    print("\n1. Filling 'delegate_models' folder...")
    print("-> Downloading BioMistral-7B into delegate_models/BioMistral-7B")
    try:
        snapshot_download(
            repo_id="BioMistral/BioMistral-7B", 
            local_dir=os.path.join(delegate_dir, "BioMistral-7B"),
            ignore_patterns=["*.safetensors"], # Use PyTorch weights to save time, or vice versa
            local_dir_use_symlinks=False
        )
        print("-> Downloading Whisper-Base into delegate_models/whisper-base")
        snapshot_download(
            repo_id="openai/whisper-base", 
            local_dir=os.path.join(delegate_dir, "whisper-base"),
            local_dir_use_symlinks=False
        )
        print("✓ Delegate models successfully stored.")
    except Exception as e:
        print(f"Error downloading delegate models: {e}")

    # Admin Models (For distinct separation as requested)
    admin_dir = os.path.join(os.getcwd(), "admin_models")
    os.makedirs(admin_dir, exist_ok=True)
    
    print("\n2. Filling 'admin_models' folder...")
    print("-> Creating linked structures for Admin Models...")
    try:
        # We can download a smaller admin-specific model, or reuse BioMistral
        snapshot_download(
            repo_id="BioMistral/BioMistral-7B", 
            local_dir=os.path.join(admin_dir, "BioMistral-7B"),
            ignore_patterns=["*.safetensors"],
            local_dir_use_symlinks=False
        )
        print("✓ Admin models successfully stored.")
    except Exception as e:
        print(f"Error downloading admin models: {e}")

    print("\n[SUCCESS] Local Model directories are fully populated!")

if __name__ == "__main__":
    download_models_locally()
