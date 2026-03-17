"""
src/train/train_face.py
────────────────────────
Train the FaceEmotionModel (EfficientNet backbone).

    python src/train/train_face.py --config configs/face.yaml [--seed 42]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm

# ── Local imports ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.datasets.face_dataset import get_face_loaders
from src.models.face_model import FaceEmotionModel
from src.utils.io import load_yaml, get_logger, get_writer, CheckpointManager
from src.utils.losses import build_criterion
from src.utils.metrics import compute_metrics, print_metrics
from src.utils.seed import seed_everything


# ── Optimizer / Scheduler factories ───────────────────────────────────────────

def build_optimizer(cfg: dict, model: nn.Module):
    name = cfg["train"]["optimizer"].lower()
    lr   = cfg["train"]["lr"]
    wd   = cfg["train"].get("weight_decay", 1e-4)
    if name == "adamw":
        return torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    if name == "adam":
        return torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    return torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9,
                           weight_decay=wd, nesterov=True)


def build_scheduler(cfg: dict, optimizer, total_steps: int):
    name = cfg["train"].get("scheduler", "cosine").lower()
    warmup = cfg["train"].get("warmup_epochs", 0)

    def warmup_lambda(step):
        if step < warmup:
            return float(step) / max(warmup, 1)
        return 1.0

    warmup_sched = torch.optim.lr_scheduler.LambdaLR(
        optimizer, lr_lambda=warmup_lambda)

    if name == "cosine":
        main_sched = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=cfg["train"]["epochs"] - warmup,
            eta_min=1e-6,
        )
    elif name == "step":
        main_sched = torch.optim.lr_scheduler.StepLR(
            optimizer, step_size=10, gamma=0.5)
    else:  # plateau
        main_sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=5)

    return warmup_sched, main_sched


# ── One epoch ─────────────────────────────────────────────────────────────────

def run_epoch(
    model: nn.Module,
    loader,
    criterion: nn.Module,
    optimizer,
    device: str,
    scaler: GradScaler,
    use_amp: bool,
    grad_clip: float,
    is_train: bool,
):
    model.train() if is_train else model.eval()

    total_loss = 0.0
    all_preds, all_targets = [], []

    pbar = tqdm(loader, desc="train" if is_train else "val ", leave=False)
    for imgs, labels in pbar:
        imgs   = imgs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with torch.set_grad_enabled(is_train):
            with autocast(enabled=use_amp):
                logits = model(imgs)
                loss   = criterion(logits, labels)

        if is_train:
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            if grad_clip > 0:
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            scaler.step(optimizer)
            scaler.update()

        total_loss += loss.item() * imgs.size(0)
        preds = logits.argmax(dim=-1).cpu().numpy()
        all_preds.append(preds)
        all_targets.append(labels.cpu().numpy())
        pbar.set_postfix(loss=f"{loss.item():.4f}")

    all_preds   = np.concatenate(all_preds)
    all_targets = np.concatenate(all_targets)
    avg_loss    = total_loss / len(loader.dataset)
    return avg_loss, all_preds, all_targets


# ── Main training loop ────────────────────────────────────────────────────────

def train(cfg_path: str, seed: int = 42) -> None:
    cfg    = load_yaml(cfg_path)
    seed_everything(seed)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger = get_logger("train_face", cfg["output"]["log_dir"])
    writer = get_writer(cfg["output"]["log_dir"])
    ckpt_mgr = CheckpointManager(
        cfg["output"]["checkpoint_dir"],
        monitor=cfg["output"]["monitor"],
        save_top_k=cfg["output"]["save_top_k"],
        logger=logger,
    )

    logger.info(f"Device: {device}  |  Config: {cfg_path}")

    # ── Data ──────────────────────────────────────────────────────────────────
    train_loader, val_loader, class_weights = get_face_loaders(cfg)

    # ── Model ─────────────────────────────────────────────────────────────────
    model = FaceEmotionModel.from_config(cfg, mode="classifier").to(device)
    logger.info(f"Params: {sum(p.numel() for p in model.parameters()):,}")

    # ── Loss / Optimizer / Scheduler ──────────────────────────────────────────
    criterion = build_criterion(cfg["loss"], cfg["num_classes"],
                                class_weights.to(device))
    optimizer = build_optimizer(cfg, model)
    warmup_sched, main_sched = build_scheduler(cfg, optimizer,
                                               len(train_loader))
    scaler = GradScaler(enabled=cfg["train"].get("amp", True))

    use_amp    = cfg["train"].get("amp", True)
    grad_clip  = cfg["train"].get("grad_clip", 1.0)
    epochs     = cfg["train"]["epochs"]
    warmup_ep  = cfg["train"].get("warmup_epochs", 0)
    class_names = cfg["classes"]

    # ── Epoch loop ─────────────────────────────────────────────────────────────
    for epoch in range(1, epochs + 1):
        # LR schedule
        if epoch <= warmup_ep:
            warmup_sched.step()
        else:
            if isinstance(main_sched,
                          torch.optim.lr_scheduler.ReduceLROnPlateau):
                pass   # stepped after val
            else:
                main_sched.step()

        # Train
        tr_loss, tr_preds, tr_targets = run_epoch(
            model, train_loader, criterion, optimizer, device,
            scaler, use_amp, grad_clip, is_train=True)
        tr_metrics = compute_metrics(tr_preds, tr_targets,
                                     class_names, cfg["num_classes"])

        # Val
        val_loss, val_preds, val_targets = run_epoch(
            model, val_loader, criterion, optimizer, device,
            scaler, use_amp, grad_clip, is_train=False)
        val_metrics = compute_metrics(val_preds, val_targets,
                                      class_names, cfg["num_classes"])

        if isinstance(main_sched,
                      torch.optim.lr_scheduler.ReduceLROnPlateau):
            main_sched.step(val_metrics["acc"])

        # Logging
        lr_now = optimizer.param_groups[0]["lr"]
        writer.add_scalar("Loss/train", tr_loss, epoch)
        writer.add_scalar("Loss/val",   val_loss, epoch)
        writer.add_scalar("Acc/train",  tr_metrics["acc"], epoch)
        writer.add_scalar("Acc/val",    val_metrics["acc"], epoch)
        writer.add_scalar("F1/val",     val_metrics["f1_macro"], epoch)
        writer.add_scalar("LR",         lr_now, epoch)

        logger.info(
            f"Epoch {epoch:03d}/{epochs}  "
            f"lr={lr_now:.2e}  "
            f"train_loss={tr_loss:.4f}  val_loss={val_loss:.4f}  "
            f"val_acc={val_metrics['acc']:.4f}  "
            f"val_f1={val_metrics['f1_macro']:.4f}"
        )

        ckpt_mgr.step(model, optimizer, epoch, {
            "val_acc": val_metrics["acc"],
            "val_f1":  val_metrics["f1_macro"],
        })

    writer.close()
    logger.info("Training complete.")
    logger.info(f"Best {ckpt_mgr.monitor}: {ckpt_mgr.best_score:.4f}")

    # Final per-class report on validation set
    val_loss, val_preds, val_targets = run_epoch(
        model, val_loader, criterion, optimizer, device,
        scaler, use_amp, grad_clip, is_train=False)
    final = compute_metrics(val_preds, val_targets, class_names, cfg["num_classes"])
    print_metrics(final, prefix="FINAL VAL")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/face.yaml")
    parser.add_argument("--seed",   type=int, default=42)
    args = parser.parse_args()
    train(args.config, args.seed)
