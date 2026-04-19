# MuseTalk Model Setup - Complete Guide

## Current Status
✅ Directories created  
⏳ Models downloading (in progress via auto_download_models.py)

## Required Model Files

### 1. **MuseTalk UNet Model** (~1.5GB) - MOST IMPORTANT
- **What**: Main lip-sync generation model
- **Status**: Downloading via script
- **Location**: `models/musetalk/pytorch_model.bin`
- **Download URL**: https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk/pytorch_model.bin

### 2. **MuseTalk Config** (small)
- **What**: UNet architecture configuration
- **Status**: Downloading via script  
- **Location**: `models/musetalk/musetalk.json`
- **Download URL**: https://huggingface.co/TMElyralab/MuseTalk/resolve/main/musetalk/musetalk.json

### 3. **SD-VAE-FT-MSE** (~335MB)
- **What**: Variational Autoencoder for image encoding/decoding
- **Status**: ✅ Already downloaded
- **Location**: `models/sd-vae-ft-mse/`
  - `config.json` ✓
  - `diffusion_pytorch_model.bin` ✓

### 4. **Whisper Tiny** (~150MB)
- **What**: Audio feature extraction model
- **Status**: Downloading via script
- **Location**: `models/whisper/tiny.pt`
- **Download URL**: https://huggingface.co/openai/whisper-tiny/resolve/main/pytorch_model.bin

### 5. **ResNet18** (~45MB)
- **What**: Backbone for face parsing
- **Status**: Downloading via script
- **Location**: `models/face-parse-bisent/resnet18-5c106cde.pth`
- **Download URL**: https://download.pytorch.org/models/resnet18-5c106cde.pth

### 6. **Face Parsing Model** (~180MB) - MANUAL DOWNLOAD REQUIRED ⚠️
- **What**: Face segmentation for blending
- **Status**: ❌ Needs manual download
- **Location**: `models/face-parse-bisent/79999_iter.pth`
- **Download URL**: https://drive.google.com/file/d/154JgKpzCPWn2q1fLzf6rLoz88n8sfB1l/view
- **Instructions**:
  1. Open the Google Drive link above
  2. Click "Download" 
  3. Rename downloaded file to `79999_iter.pth`
  4. Move to: `models/face-parse-bisent/79999_iter.pth`

### 7. **DWPose Model** (~350MB) - Only for Avatar Generation
- **What**: Pose estimation for face landmark detection
- **Status**: ❌ Optional (only needed when generating avatars)
- **Location**: `models/dwpose/dw-ll_ucoco_384.pth`
- **Download URL**: https://download.openmmlab.com/mmpose/v1/projects/rtmpose/dw-ll_ucoco_384.pth

---

## What You Need to Do NOW

### **Option A: Wait for Automatic Downloads** (Recommended)
The `auto_download_models.py` script is currently running and downloading models automatically. Just wait for it to complete (~10-30 minutes depending on internet speed).

### **Option B: Manual Download** (Faster if you have good internet)
1. Download all files from URLs listed above
2. Place them in the correct directories
3. Verify all files are present

---

## After All Models Are Downloaded

### Step 1: Verify All Models Are Present
Run this command to check:
```bash
cd C:\Users\Rayen\Desktop\testforfum\ESPRIT-PI-4DS10-25-26-Co_Win\dso1\src\avatar\LiveTalking
python -c "import os; models=['models/musetalk/pytorch_model.bin','models/musetalk/musetalk.json','models/sd-vae-ft-mse/diffusion_pytorch_model.bin','models/whisper/tiny.pt','models/face-parse-bisent/resnet18-5c106cde.pth','models/face-parse-bisent/79999_iter.pth']; [print(f'✓ {m}') if os.path.exists(m) else print(f'✗ MISSING: {m}') for m in models]"
```

### Step 2: Generate Avatar from Reference Video
You need a reference video (10-30 seconds, clear face visibility):

```bash
cd C:\Users\Rayen\Desktop\testforfum\ESPRIT-PI-4DS10-25-26-Co_Win\dso1\src\avatar\LiveTalking
python avatars/musetalk/genavatar.py --file path/to/your/video.mp4 --avatar_id musetalk_avatar
```

This will create avatar data in: `data/avatars/musetalk_avatar/`

### Step 3: Run the Application
```bash
cd C:\Users\Rayen\Desktop\testforfum\ESPRIT-PI-4DS10-25-26-Co_Win
python shared/main.py
```

Access at: http://localhost:8010/dashboard.html

---

## Troubleshooting

### "Model file not found" error
- Check which file is missing using Step 1 above
- Re-download the missing file

### "Out of memory" error
- MuseTalk requires at least 8GB VRAM
- Close other GPU applications
- Consider using a GPU with more VRAM

### Avatar generation fails
- Ensure DWPose model is downloaded
- Check that your reference video has clear face visibility
- Verify video is 10-30 seconds long

---

## Summary

**Currently happening**: Models are downloading automatically (~2-3GB total)

**You need to do**:
1. ✅ Wait for downloads to complete OR download manually
2. ⚠ Download face parsing model manually from Google Drive
3. 📹 Prepare a reference video for avatar generation
4. 🚀 Run the application

**Estimated time**: 10-30 minutes for downloads + 2-5 minutes for avatar generation
