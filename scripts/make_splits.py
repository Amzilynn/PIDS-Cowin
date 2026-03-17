"""
scripts/make_splits.py
───────────────────────
Split a flat folder dataset into train / val / test subfolders.

Input structure:
    src/
    ├── happy/    *.jpg
    ├── sad/      *.jpg
    └── ...

Output structure:
    dst/
    ├── train/
    │   ├── happy/
    │   └── ...
    ├── val/
    │   └── ...
    └── test/       (only if --test > 0)
        └── ...

Usage:
    python scripts/make_splits.py \
        --src  data/raw \
        --dst  data/splits \
        --val  0.15 \
        --test 0.10 \
        --seed 42
"""

import argparse
import random
import shutil
from pathlib import Path


IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def make_splits(
    src: str,
    dst: str,
    val_ratio: float = 0.15,
    test_ratio: float = 0.10,
    seed: int = 42,
) -> None:
    random.seed(seed)
    src_root = Path(src)
    dst_root = Path(dst)

    splits = ["train", "val"]
    if test_ratio > 0:
        splits.append("test")

    # Create output dirs
    for cls_dir in src_root.iterdir():
        if not cls_dir.is_dir():
            continue
        cls = cls_dir.name
        imgs = sorted([
            f for f in cls_dir.iterdir()
            if f.suffix.lower() in IMG_EXTS
        ])
        if not imgs:
            continue

        random.shuffle(imgs)
        n = len(imgs)
        n_test = int(n * test_ratio) if test_ratio > 0 else 0
        n_val  = int(n * val_ratio)
        n_train = n - n_val - n_test

        buckets = {
            "train": imgs[:n_train],
            "val":   imgs[n_train: n_train + n_val],
        }
        if test_ratio > 0:
            buckets["test"] = imgs[n_train + n_val:]

        for split, files in buckets.items():
            out_dir = dst_root / split / cls
            out_dir.mkdir(parents=True, exist_ok=True)
            for f in files:
                shutil.copy2(f, out_dir / f.name)

        print(f"  {cls:15s}  total={n:5d}  "
              f"train={len(buckets['train']):5d}  "
              f"val={len(buckets['val']):5d}  "
              + (f"test={len(buckets.get('test', []))}  "
                 if test_ratio > 0 else ""))

    print(f"\nSplits written to: {dst_root}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src",  required=True,
                        help="Source folder (class subdirs)")
    parser.add_argument("--dst",  required=True,
                        help="Destination folder for splits")
    parser.add_argument("--val",  type=float, default=0.15,
                        help="Fraction reserved for validation")
    parser.add_argument("--test", type=float, default=0.10,
                        help="Fraction reserved for test (0 = no test set)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    make_splits(args.src, args.dst, args.val, args.test, args.seed)
