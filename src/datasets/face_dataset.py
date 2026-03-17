"""
src/datasets/face_dataset.py
────────────────────────────
Folder-based face-emotion dataset compatible with AffectNet, RAF-DB,
FER2013, or any custom structure:

    root/
    ├── train/
    │   ├── happy/    *.jpg
    │   ├── sad/      *.jpg
    │   └── ...
    └── val/
        └── ...
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional, Callable

import cv2
import numpy as np
from PIL import Image

import albumentations as A
from albumentations.pytorch import ToTensorV2

import torch
from torch.utils.data import Dataset, DataLoader


# ── Default class order ───────────────────────────────────────────────────────
DEFAULT_CLASSES = ["neutral", "happy", "sad", "angry", "fearful", "disgusted", "surprised"]


def build_transforms(img_size: int = 224, split: str = "train") -> A.Compose:
    """Return albumentations transform pipeline."""
    mean = (0.485, 0.456, 0.406)
    std  = (0.229, 0.224, 0.225)

    if split == "train":
        return A.Compose([
            A.RandomResizedCrop(img_size, img_size, scale=(0.75, 1.0)),
            A.HorizontalFlip(p=0.5),
            A.OneOf([
                A.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1, p=1.0),
                A.ToGray(p=1.0),
            ], p=0.4),
            A.GaussNoise(var_limit=(5, 30), p=0.2),
            A.CoarseDropout(max_holes=4, max_height=32, max_width=32, p=0.2),
            A.Normalize(mean=mean, std=std),
            ToTensorV2(),
        ])
    else:
        return A.Compose([
            A.Resize(img_size, img_size),
            A.Normalize(mean=mean, std=std),
            ToTensorV2(),
        ])


class FaceDataset(Dataset):
    """
    Parameters
    ----------
    root   : path to split folder (e.g. data/splits/train/)
    classes: ordered list of class names; must match subfolder names
    split  : 'train' | 'val' | 'test'
    img_size: square resize target
    transform: optional custom albumentations Compose
    """

    def __init__(
        self,
        root: str,
        classes: Optional[List[str]] = None,
        split: str = "train",
        img_size: int = 224,
        transform: Optional[A.Compose] = None,
    ) -> None:
        self.root = Path(root)
        self.classes = classes or DEFAULT_CLASSES
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.split = split
        self.transform = transform or build_transforms(img_size, split)

        self.samples: List[Tuple[Path, int]] = []
        self._load_samples()

    def _load_samples(self) -> None:
        img_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        missing_classes = []

        for cls in self.classes:
            cls_dir = self.root / cls
            if not cls_dir.is_dir():
                missing_classes.append(cls)
                continue
            label = self.class_to_idx[cls]
            for img_path in cls_dir.iterdir():
                if img_path.suffix.lower() in img_extensions:
                    self.samples.append((img_path, label))

        if missing_classes:
            print(f"[FaceDataset] WARNING: missing class folders: {missing_classes}")

        print(f"[FaceDataset] {self.split}: {len(self.samples)} images | "
              f"{len(self.classes)} classes")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]

        img = cv2.imread(str(img_path))
        if img is None:
            # fallback: PIL
            img = np.array(Image.open(img_path).convert("RGB"))
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        augmented = self.transform(image=img)
        return augmented["image"], label

    # ── class weights for imbalanced datasets ─────────────────────────────────
    def class_weights(self) -> torch.Tensor:
        counts = torch.zeros(len(self.classes))
        for _, label in self.samples:
            counts[label] += 1
        weights = counts.sum() / (len(self.classes) * counts.clamp(min=1))
        return weights


# ── Factory helpers ───────────────────────────────────────────────────────────

def get_face_loaders(cfg: dict) -> Tuple[DataLoader, DataLoader]:
    """Build train/val DataLoaders from a config dict (face.yaml)."""
    classes = cfg.get("classes", DEFAULT_CLASSES)
    img_size = cfg["data"]["img_size"]

    train_ds = FaceDataset(cfg["data"]["train_dir"], classes=classes,
                           split="train", img_size=img_size)
    val_ds   = FaceDataset(cfg["data"]["val_dir"],   classes=classes,
                           split="val",   img_size=img_size)

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
    return train_loader, val_loader, train_ds.class_weights()
