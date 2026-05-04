# MuseTalk Setup Guide

This guide will help you set up and run the project with **MuseTalk**, a high-quality lip-sync model.

## Prerequisites

- **GPU**: NVIDIA RTX 3080Ti or better recommended (MuseTalk is more GPU-intensive than Wav2Lip)
- **VRAM**: At least 8GB VRAM
- **Python**: 3.10+
- **PyTorch**: 2.5.0 with CUDA 12.4 support

## Step 1: Download MuseTalk Models

You need to download the MuseTalk pretrained models and place them in the correct directories.

### Option A: Download from LiveTalking Official Sources

1. **Download from Quark Cloud Drive**: <https://pan.quark.cn/s/83a750323ef0>
2. **Download from Google Drive**: <https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ?usp=sharing>

### Required Model Files

After downloading, you need to organize the files as follows:

#### 1. Create `models` directory
```
dso1/src/avatar/LiveTalking/models/
```

Place these files in the `models/` directory:
- `musetalk.pth` - Main MuseTalk model weights
- `whisper/` - Whisper audio feature extraction model directory

#### 2. Create MuseTalk Avatar Data
```
dso1/src/avatar/LiveTalking/data/avatars/musetalk_avatar/
```

This directory should contain:
- `full_imgs/` - Extracted full frames from your reference video
- `mask/` - Face segmentation masks
- `coords.pkl` - Bounding box coordinates for face regions
- `mask_coords.pkl` - Coordinates for mask regions  
- `latents.pt` - Pre-computed VAE latents
- `avator_info.json` - Avatar metadata

## Step 2: Generate Avatar Data (If Not Provided)

If you don't have pre-generated avatar data, you need to create it from a reference video:

1. **Prepare a reference video** (10-30 seconds, clear face visibility, good lighting)
2. **Run the avatar generation script**:

```bash
cd dso1/src/avatar/LiveTalking
python avatars/musetalk/genavatar.py --video_path /path/to/your/video.mp4 --avatar_id musetalk_avatar
```

This will:
- Extract frames
- Generate face masks
- Compute VAE latents
- Save all data to `data/avatars/musetalk_avatar/`

## Step 3: Install Dependencies

Ensure all MuseTalk dependencies are installed:

```bash
cd dso1/src/avatar/LiveTalking
pip install -r requirements.txt
```

The key MuseTalk-specific dependencies already in `requirements.txt`:
- `diffusers` - For VAE and UNet
- `accelerate` - Model optimization
- `omegaconf` - Configuration management
- `typeguard==2.13.3` - Type checking
- `onnxruntime-gpu` - GPU acceleration

## Step 4: Verify Setup

Before running the full application, verify the setup:

```bash
cd dso1/src/avatar/LiveTalking

# Check if models exist
ls models/

# Check if avatar data exists
ls data/avatars/musetalk_avatar/
```

Expected structure:
```
models/
├── musetalk.pth
└── whisper/

data/avatars/musetalk_avatar/
├── full_imgs/
├── mask/
├── coords.pkl
├── mask_coords.pkl
├── latents.pt
└── avator_info.json
```

## Step 5: Run with MuseTalk

### Using the Main Orchestrator (Recommended)

From the project root:

```bash
python shared/main.py
```

This will automatically start the LiveTalking server with MuseTalk model.

### Manual Testing

For direct testing without the orchestrator:

```bash
cd dso1/src/avatar/LiveTalking
python app.py --transport webrtc --model musetalk --avatar_id musetalk_avatar
```

## Step 6: Access the Application

Once running, access the application:

1. **WebRTC Interface**: `http://localhost:8010/dashboard.html`
2. **API Interface**: `http://localhost:8010/webrtcapi.html`

## Troubleshooting

### Issue: "Model file not found"
**Solution**: Ensure `musetalk.pth` is in `dso1/src/avatar/LiveTalking/models/`

### Issue: "Avatar data not found"
**Solution**: Run the avatar generation script (Step 2) or download pre-made avatar data

### Issue: "Out of memory"
**Solution**: 
- Reduce batch size: Add `--batch_size 8` to the command
- Close other GPU-intensive applications
- Consider using Wav2Lip instead if GPU is insufficient

### Issue: "Whisper model loading failed"
**Solution**: Ensure the whisper model directory is properly structured:
```
models/whisper/
├── model.pt
└── (other whisper files)
```

## Performance Notes

According to the LiveTalking documentation:

| GPU Model | Expected FPS |
|-----------|--------------|
| RTX 3080Ti | ~42 FPS |
| RTX 3090 | ~45 FPS |
| RTX 4090 | ~72 FPS |

**Note**: MuseTalk provides higher quality lip-sync compared to Wav2Lip but requires more GPU resources.

## Switching Back to Wav2Lip

If you need to switch back to Wav2Lip:

1. Edit `shared/main.py`:
   ```python
   [sys.executable, "app.py", "--transport", "webrtc", "--model", "wav2lip", "--avatar_id", "wav2lip256_avatar1"]
   ```

2. Ensure Wav2Lip models and avatar data are in place

## Additional Resources

- **LiveTalking Documentation**: <https://livetalking-doc.readthedocs.io/>
- **MuseTalk Original Repository**: <https://github.com/TMElyralab/MuseTalk>
- **English README**: `dso1/src/avatar/LiveTalking/README-EN.md`

## Next Steps

After successful setup:
1. Test with different reference videos
2. Explore voice cloning features
3. Integrate with the DSO2 API endpoints
4. Customize avatar behaviors
