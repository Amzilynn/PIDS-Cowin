"""
src/utils/losses.py
────────────────────
Custom loss functions:
  - FocalLoss          : down-weights easy examples; great for class imbalance
  - LabelSmoothingLoss : prevents over-confidence
  - build_criterion    : factory used by training scripts
"""

from typing import Optional, List
import torch
import torch.nn as nn
import torch.nn.functional as F


# ── Focal Loss ────────────────────────────────────────────────────────────────

class FocalLoss(nn.Module):
    """
    Multi-class focal loss.
    FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)

    Parameters
    ----------
    gamma : focusing parameter (0 = standard CE, 2 works well)
    alpha : per-class weights tensor or None
    """

    def __init__(
        self,
        gamma: float = 2.0,
        alpha: Optional[torch.Tensor] = None,
        reduction: str = "mean",
    ) -> None:
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha
        self.reduction = reduction

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        log_p = F.log_softmax(logits, dim=-1)
        p     = torch.exp(log_p)

        if self.alpha is not None:
            alpha = self.alpha.to(logits.device)
            log_p = log_p * alpha.unsqueeze(0)

        focal_weight = (1 - p) ** self.gamma
        loss = -focal_weight * log_p
        loss = loss.gather(dim=-1, index=targets.unsqueeze(1)).squeeze(1)

        if self.reduction == "mean":
            return loss.mean()
        if self.reduction == "sum":
            return loss.sum()
        return loss


# ── Label Smoothing Loss ──────────────────────────────────────────────────────

class LabelSmoothingLoss(nn.Module):
    """Cross-entropy with label smoothing."""

    def __init__(self, num_classes: int, smoothing: float = 0.1) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.smoothing   = smoothing
        self.confidence  = 1.0 - smoothing

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        log_probs = F.log_softmax(logits, dim=-1)
        # Smooth targets
        with torch.no_grad():
            smooth_targets = torch.full_like(log_probs,
                                             self.smoothing / (self.num_classes - 1))
            smooth_targets.scatter_(1, targets.unsqueeze(1), self.confidence)
        return -(smooth_targets * log_probs).sum(dim=-1).mean()


# ── Factory ───────────────────────────────────────────────────────────────────

def build_criterion(
    cfg: dict,
    num_classes: int,
    class_weights: Optional[torch.Tensor] = None,
) -> nn.Module:
    """
    Build loss from config.  cfg is the 'loss' sub-dict from a YAML file.

    Supported loss names: cross_entropy, focal, label_smooth
    """
    name = cfg.get("name", "cross_entropy").lower()

    if name == "focal":
        alpha = None
        if cfg.get("focal_alpha") is not None:
            alpha = torch.tensor(cfg["focal_alpha"], dtype=torch.float32)
        elif class_weights is not None:
            alpha = class_weights
        return FocalLoss(gamma=cfg.get("focal_gamma", 2.0), alpha=alpha)

    if name == "label_smooth":
        return LabelSmoothingLoss(num_classes,
                                  smoothing=cfg.get("label_smoothing", 0.1))

    # Default: standard cross-entropy (with optional class weighting)
    weight = class_weights if class_weights is not None else None
    return nn.CrossEntropyLoss(
        weight=weight,
        label_smoothing=cfg.get("label_smoothing", 0.0),
    )
