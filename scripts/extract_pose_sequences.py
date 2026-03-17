"""
scripts/extract_pose_sequences.py
───────────────────────────────────
Pre-extract MediaPipe Pose keypoints from video files and save as .npy arrays.
Also generates a labels CSV for the PoseDataset.

Input:
    video_dir/
    ├── happy/
    │   ├── clip001.mp4
    │   └── ...
    ├── sad/
    └── ...

Output:
    out_dir/
    ├── happy_clip001.npy    # shape (T, 132)  T can vary per clip
    └── ...
    out_dir/labels.csv       # stem, label_index

Usage:
    python scripts/extract_pose_sequences.py \
        --video_dir  data/videos \
        --out_dir    data/pose_npy \
        --classes    neutral happy sad angry fearful disgusted surprised
"""

import argparse
import csv
from pathlib import Path
from typing import List, Optional

import cv2
import mediapipe as mp
import numpy as np
from tqdm import tqdm

mp_pose = mp.solutions.pose

VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def extract_pose_from_video(
    video_path: Path,
    pose_estimator: mp_pose.Pose,
) -> Optional[np.ndarray]:
    """
    Extract per-frame pose keypoints from a single video.

    Returns
    -------
    np.ndarray | None
        Shape (T, 132) where 132 = 33 landmarks × (x, y, z, visibility).
        Returns None if video cannot be opened or has 0 valid frames.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None

    frames: List[np.ndarray] = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = pose_estimator.process(rgb)
        rgb.flags.writeable = True

        if result.pose_landmarks:
            kps = np.array(
                [[lm.x, lm.y, lm.z, lm.visibility]
                 for lm in result.pose_landmarks.landmark],
                dtype=np.float32,
            ).flatten()   # (132,)
        else:
            kps = np.zeros(132, dtype=np.float32)

        frames.append(kps)

    cap.release()
    return np.stack(frames, axis=0) if frames else None   # (T, 132)


def extract_all(
    video_dir: str,
    out_dir: str,
    classes: List[str],
    min_detection: float = 0.5,
    min_tracking:  float = 0.5,
) -> None:
    video_root = Path(video_dir)
    out_root   = Path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)

    class_to_idx = {c: i for i, c in enumerate(classes)}
    label_rows   = []

    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=min_detection,
        min_tracking_confidence=min_tracking,
    )

    for cls in classes:
        cls_dir = video_root / cls
        if not cls_dir.is_dir():
            print(f"[SKIP] class folder not found: {cls_dir}")
            continue

        video_files = [f for f in cls_dir.iterdir()
                       if f.suffix.lower() in VIDEO_EXTS]
        print(f"\n{cls}: {len(video_files)} videos")

        for vf in tqdm(video_files, desc=cls):
            stem    = f"{cls}_{vf.stem}"
            npy_out = out_root / f"{stem}.npy"

            if npy_out.exists():
                label_rows.append((stem, class_to_idx[cls]))
                continue

            seq = extract_pose_from_video(vf, pose)
            if seq is None or seq.shape[0] == 0:
                print(f"  [WARN] skipped (no landmarks): {vf.name}")
                continue

            np.save(npy_out, seq)
            label_rows.append((stem, class_to_idx[cls]))

    pose.close()

    # Write label CSV
    csv_path = out_root / "labels.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(label_rows)

    print(f"\nExtracted {len(label_rows)} sequences → {out_root}")
    print(f"Labels CSV: {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_dir", required=True,
                        help="Root folder with class subfolders of videos")
    parser.add_argument("--out_dir",   required=True,
                        help="Where to save .npy files and labels.csv")
    parser.add_argument("--classes",   nargs="+",
                        default=["neutral", "happy", "sad", "angry",
                                 "fearful", "disgusted", "surprised"])
    parser.add_argument("--min_detection", type=float, default=0.5)
    parser.add_argument("--min_tracking",  type=float, default=0.5)
    args = parser.parse_args()

    extract_all(
        args.video_dir,
        args.out_dir,
        args.classes,
        args.min_detection,
        args.min_tracking,
    )
