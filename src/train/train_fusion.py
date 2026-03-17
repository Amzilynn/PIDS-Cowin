"""
src/train/train_fusion.py
──────────────────────────
Train the FusionModel (face + pose late fusion).

Loads pretrained face and pose checkpoints, freezes their encoders
(unless freeze_branches: false), then trains the fusion MLP head.

    python src/train/train_fusion.py \
        --config  configs/fusion.yaml \
        --face_cfg  configs/face.yaml \
        --pose_cfg  configs/pose.yaml \
        [--seed 42]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.cuda.amp import GradScaler, autocast
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.datasets.fusion_dataset import get_fusion_loaders
from src.models.fusion_model import FusionModel
from src.utils.io import load_yaml, get_logger, get_writer, CheckpointManager
from src.utils.losses import build_criterion
from src.utils.metrics import compute_metrics, print_metrics
from src.utils.seed import seed_everything


def build_optimizer(cfg, model):
    name = cfg["train"]["optimizer"].lower()
    lr, wd = cfg["train"]["lr"], cfg["train"].get("weight_decay", 1e-4)
    # Only optimise non-frozen parameters
    params = [p for p in model.parameters() if p.requires_grad]
    if name == "adamw":
        return torch.optim.AdamW(params, lr=lr, weight_decay=wd)
    if name == "adam":
        return torch.optim.Adam(params, lr=lr, weight_decay=wd)
    return torch.optim.SGD(params, lr=lr, momentum=0.9,
                           weight_decay=wd, nesterov=True)


def build_scheduler(cfg, optimizer):
    name   = cfg["train"].get("scheduler", "cosine").lower()
    warmup = cfg["train"].get("warmup_epochs", 0)

    warmup_sched = torch.optim.lr_scheduler.LambdaLR(
        optimizer,
        lr_lambda=lambda e: float(e) / max(warmup, 1) if e < warmup else 1.0)

    if name == "cosine":
        main_sched = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=cfg["train"]["epochs"] - warmup, eta_min=1e-6)
    else:
        main_sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=5)

    return warmup_sched, main_sched


def run_epoch(model, loader, criterion, optimizer, device,
              scaler, use_amp, grad_clip, is_train):
    model.train() if is_train else model.eval()
    total_loss, all_preds, all_targets = 0.0, [], []

    pbar = tqdm(loader, desc="train" if is_train else "val ", leave=False)
    for face_imgs, pose_seqs, labels in pbar:
        face_imgs = face_imgs.to(device, non_blocking=True)
        pose_seqs = pose_seqs.to(device, non_blocking=True)
        labels    = labels.to(device, non_blocking=True)

        with torch.set_grad_enabled(is_train):
            with autocast(enabled=use_amp):
                logits = model(face_imgs, pose_seqs)
                loss   = criterion(logits, labels)

        if is_train:
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            if grad_clip > 0:
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(
                    [p for p in model.parameters() if p.requires_grad],
                    grad_clip)
            scaler.step(optimizer)
            scaler.update()

        total_loss += loss.item() * face_imgs.size(0)
        all_preds.append(logits.argmax(-1).cpu().numpy())
        all_targets.append(labels.cpu().numpy())
        pbar.set_postfix(loss=f"{loss.item():.4f}")

    return (total_loss / len(loader.dataset),
            np.concatenate(all_preds),
            np.concatenate(all_targets))


def train(cfg_path: str, face_cfg_path: str, pose_cfg_path: str,
          seed: int = 42) -> None:

    cfg      = load_yaml(cfg_path)
    face_cfg = load_yaml(face_cfg_path)
    pose_cfg = load_yaml(pose_cfg_path)
    seed_everything(seed)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger = get_logger("train_fusion", cfg["output"]["log_dir"])
    writer = get_writer(cfg["output"]["log_dir"])
    ckpt_mgr = CheckpointManager(
        cfg["output"]["checkpoint_dir"],
        monitor=cfg["output"]["monitor"],
        save_top_k=cfg["output"]["save_top_k"],
        logger=logger,
    )
    logger.info(f"Device: {device} | Fusion type: {cfg['model']['fusion_type']}")

    train_loader, val_loader = get_fusion_loaders(cfg)

    model = FusionModel.from_config(cfg, face_cfg, pose_cfg,
                                    device=device).to(device)

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total     = sum(p.numel() for p in model.parameters())
    logger.info(f"Trainable: {trainable:,} / Total: {total:,}")

    criterion    = build_criterion(cfg["loss"], cfg["num_classes"])
    optimizer    = build_optimizer(cfg, model)
    warmup_sched, main_sched = build_scheduler(cfg, optimizer)
    scaler       = GradScaler(enabled=cfg["train"].get("amp", True))
    use_amp      = cfg["train"].get("amp", True)
    grad_clip    = cfg["train"].get("grad_clip", 1.0)
    epochs       = cfg["train"]["epochs"]
    warmup_ep    = cfg["train"].get("warmup_epochs", 0)
    class_names  = cfg["classes"]

    for epoch in range(1, epochs + 1):
        if epoch <= warmup_ep:
            warmup_sched.step()
        elif not isinstance(main_sched,
                            torch.optim.lr_scheduler.ReduceLROnPlateau):
            main_sched.step()

        tr_loss, tr_preds, tr_tgts = run_epoch(
            model, train_loader, criterion, optimizer,
            device, scaler, use_amp, grad_clip, True)
        val_loss, val_preds, val_tgts = run_epoch(
            model, val_loader, criterion, optimizer,
            device, scaler, use_amp, grad_clip, False)

        tr_m  = compute_metrics(tr_preds,  tr_tgts,  class_names, cfg["num_classes"])
        val_m = compute_metrics(val_preds, val_tgts, class_names, cfg["num_classes"])

        if isinstance(main_sched,
                      torch.optim.lr_scheduler.ReduceLROnPlateau):
            main_sched.step(val_m["f1_macro"])

        lr_now = optimizer.param_groups[0]["lr"]
        for tag, v in [
            ("Loss/train", tr_loss), ("Loss/val", val_loss),
            ("Acc/val",  val_m["acc"]), ("F1/val", val_m["f1_macro"]),
            ("LR", lr_now),
        ]:
            writer.add_scalar(tag, v, epoch)

        logger.info(
            f"Epoch {epoch:03d}/{epochs}  lr={lr_now:.2e}  "
            f"val_loss={val_loss:.4f}  val_acc={val_m['acc']:.4f}  "
            f"val_f1={val_m['f1_macro']:.4f}"
        )
        ckpt_mgr.step(model, optimizer, epoch, {
            "val_acc": val_m["acc"],
            "val_f1":  val_m["f1_macro"],
        })

    writer.close()
    logger.info(f"Best {ckpt_mgr.monitor}: {ckpt_mgr.best_score:.4f}")
    val_loss, val_preds, val_tgts = run_epoch(
        model, val_loader, criterion, optimizer,
        device, scaler, use_amp, grad_clip, False)
    print_metrics(compute_metrics(val_preds, val_tgts, class_names,
                                  cfg["num_classes"]), prefix="FINAL VAL")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config",    default="configs/fusion.yaml")
    parser.add_argument("--face_cfg",  default="configs/face.yaml")
    parser.add_argument("--pose_cfg",  default="configs/pose.yaml")
    parser.add_argument("--seed",      type=int, default=42)
    args = parser.parse_args()
    train(args.config, args.face_cfg, args.pose_cfg, args.seed)
