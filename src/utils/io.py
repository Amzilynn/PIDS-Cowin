"""
src/utils/io.py
────────────────
I/O helpers:
  - YAML config loading
  - Checkpoint save / load
  - Logger setup (console + file)
  - TensorBoard writer factory
"""

import os
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter


# ── YAML ──────────────────────────────────────────────────────────────────────

def load_yaml(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Logger ────────────────────────────────────────────────────────────────────

def get_logger(name: str, log_dir: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter("[%(asctime)s] %(levelname)s  %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    # Console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File (optional)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(Path(log_dir) / f"{name}.log")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


# ── TensorBoard ───────────────────────────────────────────────────────────────

def get_writer(log_dir: str) -> SummaryWriter:
    os.makedirs(log_dir, exist_ok=True)
    return SummaryWriter(log_dir=log_dir)


# ── Checkpointing ─────────────────────────────────────────────────────────────

def save_checkpoint(
    ckpt_dir: str,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    metrics: Dict[str, float],
    is_best: bool = False,
    filename: Optional[str] = None,
) -> None:
    os.makedirs(ckpt_dir, exist_ok=True)
    fname = filename or f"epoch_{epoch:03d}.pth"
    path  = Path(ckpt_dir) / fname

    torch.save({
        "epoch":            epoch,
        "model_state_dict": model.state_dict(),
        "optim_state_dict": optimizer.state_dict(),
        "metrics":          metrics,
    }, path)

    if is_best:
        shutil.copy(path, Path(ckpt_dir) / "best.pth")


def load_checkpoint(
    ckpt_path: str,
    model: nn.Module,
    optimizer: Optional[torch.optim.Optimizer] = None,
    device: str = "cuda",
) -> Dict[str, Any]:
    state = torch.load(ckpt_path, map_location=device)
    model.load_state_dict(state["model_state_dict"])
    if optimizer and "optim_state_dict" in state:
        optimizer.load_state_dict(state["optim_state_dict"])
    return state


# ── Checkpoint manager (keeps top-k) ─────────────────────────────────────────

class CheckpointManager:
    """Keeps only the top-k checkpoints ranked by a monitored metric."""

    def __init__(
        self,
        ckpt_dir: str,
        monitor: str = "val_acc",
        mode: str = "max",
        save_top_k: int = 3,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.ckpt_dir  = Path(ckpt_dir)
        self.monitor   = monitor
        self.mode      = mode
        self.save_top_k = save_top_k
        self.logger    = logger or get_logger("CheckpointManager")
        self.history: list = []   # [(score, path)]
        self.best_score = float("-inf") if mode == "max" else float("inf")

    def step(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        metrics: Dict[str, float],
    ) -> bool:
        score   = metrics.get(self.monitor, 0.0)
        is_best = (score > self.best_score if self.mode == "max"
                   else score < self.best_score)
        if is_best:
            self.best_score = score

        fname = f"epoch_{epoch:03d}_{self.monitor}_{score:.4f}.pth"
        save_checkpoint(str(self.ckpt_dir), model, optimizer, epoch,
                        metrics, is_best=is_best, filename=fname)

        self.history.append((score, self.ckpt_dir / fname))
        self.history.sort(key=lambda t: t[0],
                          reverse=(self.mode == "max"))

        # Remove worst checkpoints beyond top-k
        while len(self.history) > self.save_top_k:
            _, old_path = self.history.pop()
            if old_path.exists():
                old_path.unlink()
                self.logger.info(f"Removed old ckpt: {old_path.name}")

        self.logger.info(
            f"Epoch {epoch:03d} | {self.monitor}={score:.4f} "
            f"{'[BEST]' if is_best else ''} | best={self.best_score:.4f}"
        )
        return is_best
