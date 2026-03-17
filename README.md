# stress_emotion_multimodal

A **PyTorch + CUDA** multimodal pipeline for **facial emotion recognition** and **body-pose stress detection**.

## Architecture

```
Webcam / Video
    │
    ├──► Face crop  ──► FaceEmotionModel (EfficientNet-B2)  ──► face_feat (512-d)
    │                                                                 │
    └──► Pose seq   ──► PoseModel (LSTM + Attn)             ──► pose_feat (256-d)
                                                                      │
                                                            FusionModel (MLP)
                                                                      │
                                                     emotions + stress score (real-time)
```

## Supported Emotions

`neutral · happy · sad · angry · fearful · disgusted · surprised · stressed`

## Quick-Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. (Optional) split your raw dataset
python scripts/make_splits.py --src data/raw --dst data/splits --val 0.15 --test 0.10

# 3. Extract pose sequences from videos
python scripts/extract_pose_sequences.py --video_dir data/videos --out_dir data/pose_npy

# 4. Train face model
python src/train/train_face.py --config configs/face.yaml

# 5. Train pose model
python src/train/train_pose.py --config configs/pose.yaml

# 6. Train fusion model
python src/train/train_fusion.py --config configs/fusion.yaml

# 7. Live webcam inference
python src/infer/webcam_infer.py --config configs/inference.yaml
```

## Dataset Folder Format

```
data/splits/
├── train/
│   ├── angry/
│   ├── happy/
│   ├── sad/
│   ├── neutral/
│   ├── fearful/
│   ├── disgusted/
│   └── surprised/
└── val/
    └── ...
```

Compatible with **AffectNet**, **RAF-DB**, **FER2013**, or any custom folder dataset.

## Hardware

Tested on RTX 3090 / 4090 with CUDA 12.x.  
Mixed-precision (AMP) enabled by default — reduces VRAM ~40 %.
