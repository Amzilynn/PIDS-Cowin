"""
src/datasets/pose_dataset.py
─────────────────────────────
Loads pre-extracted MediaPipe Pose keypoint sequences (numpy *.npy files).

Expected layout produced by scripts/extract_pose_sequences.py:
    data/pose_npy/
    ├── subject01_clip001.npy   # shape (T, 132)  — T frames, 33*4 features
    └── ...

Label CSV columns: filename (stem), label (int 0..N-1)
    subject01_clip001, 2
    ...
"""

from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd

import torch
from torch.utils.data import Dataset, DataLoader


class PoseDataset(Dataset):
    """
    Parameters
    ----------
    npy_dir   : folder containing *.npy sequence files
    label_csv : CSV with columns [filename (no ext), label]
    seq_len   : fixed window length (frames); shorter clips are zero-padded
    stride    : sliding window stride for sequences longer than seq_len
    split     : 'train' | 'val' | 'test'  (for augmentation control)
    """

    def __init__(
        self,
        npy_dir: str,
        label_csv: str,
        seq_len: int = 60,
        stride: int = 30,
        split: str = "train",
    ) -> None:
        self.npy_dir = Path(npy_dir)
        self.seq_len = seq_len
        self.stride  = stride
        self.split   = split

        df = pd.read_csv(label_csv, header=None, names=["filename", "label"])
        df["filename"] = df["filename"].astype(str).str.strip()

        # Build (file_path, start_frame, label) windows
        self.windows: List[Tuple[Path, int, int]] = []
        self._build_windows(df)

        print(f"[PoseDataset] {split}: {len(self.windows)} windows | "
              f"seq_len={seq_len} | stride={stride}")

    def _build_windows(self, df: pd.DataFrame) -> None:
        for _, row in df.iterrows():
            npy_path = self.npy_dir / f"{row['filename']}.npy"
            if not npy_path.exists():
                continue
            seq = np.load(npy_path, mmap_mode="r")
            T = seq.shape[0]
            if T <= self.seq_len:
                self.windows.append((npy_path, 0, int(row["label"])))
            else:
                for start in range(0, T - self.seq_len + 1, self.stride):
                    self.windows.append((npy_path, start, int(row["label"])))

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        path, start, label = self.windows[idx]
        seq = np.load(path).astype(np.float32)   # (T, 132)

        window = seq[start: start + self.seq_len]

        # Zero-pad if clip is shorter than seq_len
        if window.shape[0] < self.seq_len:
            pad = np.zeros((self.seq_len - window.shape[0], window.shape[1]),
                           dtype=np.float32)
            window = np.concatenate([window, pad], axis=0)

        # ── Training augmentation on keypoints ────────────────────────────────
        if self.split == "train":
            # Gaussian jitter on x,y,z coordinates
            noise = np.random.normal(0, 0.005, window.shape).astype(np.float32)
            window = window + noise
            # Random temporal flip
            if np.random.rand() < 0.3:
                window = window[::-1].copy()

        return torch.from_numpy(window), label     # (seq_len, 132), int


# ── Factory helpers ───────────────────────────────────────────────────────────

def get_pose_loaders(cfg: dict) -> Tuple[DataLoader, DataLoader]:
    """Build train/val DataLoaders from pose.yaml config dict."""
    train_ds = PoseDataset(
        npy_dir=cfg["data"]["pose_npy_dir"],
        label_csv=cfg["data"]["label_csv"],
        seq_len=cfg["data"]["seq_len"],
        stride=cfg["data"]["stride"],
        split="train",
    )
    val_ds = PoseDataset(
        npy_dir=cfg["data"]["pose_npy_dir"],
        label_csv=cfg["data"]["label_csv"],
        seq_len=cfg["data"]["seq_len"],
        stride=cfg["data"]["seq_len"],   # no overlap for validation
        split="val",
    )
    train_loader = DataLoader(
        train_ds,
        batch_size=cfg["train"]["batch_size"],
        shuffle=True,
        num_workers=cfg["data"]["num_workers"],
        pin_memory=cfg["data"].get("pin_memory", True),
        drop_last=True,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=cfg["train"]["batch_size"] * 2,
        shuffle=False,
        num_workers=cfg["data"]["num_workers"],
        pin_memory=cfg["data"].get("pin_memory", True),
    )
    return train_loader, val_loader
