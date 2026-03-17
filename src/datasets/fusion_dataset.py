"""
src/datasets/fusion_dataset.py
───────────────────────────────
Paired dataset that returns (face_image, pose_sequence, label).

Requires both a folder-based face dataset AND a matching pose-npy directory
with a shared label CSV.  Each sample is identified by a unique clip stem.

CSV format:  clip_stem, label
    happy_clip001, 1
    ...

Face image is expected at:
    data/splits/{split}/{class_name}/{clip_stem}.jpg   (or .png)

Pose sequence is expected at:
    data/pose_npy/{clip_stem}.npy
"""

from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np
import pandas as pd
from PIL import Image

import albumentations as A
from albumentations.pytorch import ToTensorV2

import torch
from torch.utils.data import Dataset, DataLoader

from src.datasets.face_dataset import build_transforms, DEFAULT_CLASSES


class FusionDataset(Dataset):
    """
    Parameters
    ----------
    face_root   : split root folder (e.g. data/splits/train/)
    npy_dir     : pre-extracted pose sequences
    label_csv   : shared CSV (clip_stem, label)
    classes     : ordered emotion names
    seq_len     : pose sequence length
    stride      : sliding window stride
    split       : 'train' | 'val'
    img_size    : face image resize
    """

    def __init__(
        self,
        face_root: str,
        npy_dir: str,
        label_csv: str,
        classes: Optional[List[str]] = None,
        seq_len: int = 60,
        stride: int = 30,
        split: str = "train",
        img_size: int = 224,
    ) -> None:
        self.face_root = Path(face_root)
        self.npy_dir   = Path(npy_dir)
        self.classes   = classes or DEFAULT_CLASSES
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.seq_len   = seq_len
        self.stride    = stride
        self.split     = split
        self.img_transform = build_transforms(img_size, split)

        df = pd.read_csv(label_csv, header=None, names=["stem", "label"])
        df["stem"]  = df["stem"].astype(str).str.strip()
        df["label"] = df["label"].astype(int)

        self.windows: List[Tuple[Path, Path, int, int]] = []
        self._build_windows(df)

        print(f"[FusionDataset] {split}: {len(self.windows)} windows")

    def _find_face_image(self, stem: str, label: int) -> Optional[Path]:
        """Locate face image under any class subfolder."""
        cls_name = self.classes[label]
        for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            p = self.face_root / cls_name / f"{stem}{ext}"
            if p.exists():
                return p
        # Fallback: search all class folders
        for ext in [".jpg", ".jpeg", ".png", ".bmp"]:
            for cls in self.classes:
                p = self.face_root / cls / f"{stem}{ext}"
                if p.exists():
                    return p
        return None

    def _build_windows(self, df: pd.DataFrame) -> None:
        for _, row in df.iterrows():
            npy_path = self.npy_dir / f"{row['stem']}.npy"
            face_path = self._find_face_image(row["stem"], row["label"])

            if npy_path.exists() and face_path is not None:
                seq = np.load(npy_path, mmap_mode="r")
                T = seq.shape[0]
                if T <= self.seq_len:
                    self.windows.append((face_path, npy_path, 0, row["label"]))
                else:
                    for start in range(0, T - self.seq_len + 1, self.stride):
                        self.windows.append((face_path, npy_path, start, row["label"]))

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, idx: int):
        face_path, npy_path, start, label = self.windows[idx]

        # ── Face image ────────────────────────────────────────────────────────
        img = cv2.imread(str(face_path))
        if img is None:
            img = np.array(Image.open(face_path).convert("RGB"))
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_tensor = self.img_transform(image=img)["image"]   # (3, H, W)

        # ── Pose sequence ─────────────────────────────────────────────────────
        seq = np.load(npy_path).astype(np.float32)
        window = seq[start: start + self.seq_len]
        if window.shape[0] < self.seq_len:
            pad = np.zeros((self.seq_len - window.shape[0], window.shape[1]),
                           dtype=np.float32)
            window = np.concatenate([window, pad], axis=0)
        if self.split == "train" and np.random.rand() < 0.3:
            window = window[::-1].copy()
        pose_tensor = torch.from_numpy(window)                 # (seq_len, 132)

        return face_tensor, pose_tensor, label


# ── Factory helpers ───────────────────────────────────────────────────────────

def get_fusion_loaders(cfg: dict) -> Tuple[DataLoader, DataLoader]:
    """Build train/val DataLoaders from fusion.yaml config dict."""
    classes = cfg.get("classes", DEFAULT_CLASSES)
    train_ds = FusionDataset(
        face_root=cfg["data"]["train_dir"],
        npy_dir=cfg["data"]["pose_npy_dir"],
        label_csv=cfg["data"]["label_csv"],
        classes=classes,
        seq_len=cfg["data"]["seq_len"],
        stride=cfg["data"]["stride"],
        split="train",
        img_size=cfg["data"]["img_size"],
    )
    val_ds = FusionDataset(
        face_root=cfg["data"]["val_dir"],
        npy_dir=cfg["data"]["pose_npy_dir"],
        label_csv=cfg["data"]["label_csv"],
        classes=classes,
        seq_len=cfg["data"]["seq_len"],
        stride=cfg["data"]["seq_len"],
        split="val",
        img_size=cfg["data"]["img_size"],
    )
    bs = cfg["train"]["batch_size"]
    nw = cfg["data"]["num_workers"]
    train_loader = DataLoader(train_ds, batch_size=bs, shuffle=True,
                              num_workers=nw, pin_memory=True, drop_last=True)
    val_loader   = DataLoader(val_ds,   batch_size=bs * 2, shuffle=False,
                              num_workers=nw, pin_memory=True)
    return train_loader, val_loader
