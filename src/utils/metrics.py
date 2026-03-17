"""
src/utils/metrics.py
─────────────────────
Evaluation helpers: accuracy, per-class accuracy, macro F1,
confusion matrix, and a pretty terminal print-out.
"""

from typing import List, Optional, Dict

import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    classification_report,
)


def accuracy(preds: np.ndarray, targets: np.ndarray) -> float:
    return float((preds == targets).mean())


def per_class_accuracy(
    preds: np.ndarray,
    targets: np.ndarray,
    num_classes: int,
) -> np.ndarray:
    acc = np.zeros(num_classes)
    for c in range(num_classes):
        mask = targets == c
        if mask.sum() == 0:
            acc[c] = float("nan")
        else:
            acc[c] = (preds[mask] == c).mean()
    return acc


def macro_f1(preds: np.ndarray, targets: np.ndarray) -> float:
    return float(f1_score(targets, preds, average="macro", zero_division=0))


def weighted_f1(preds: np.ndarray, targets: np.ndarray) -> float:
    return float(f1_score(targets, preds, average="weighted", zero_division=0))


def compute_metrics(
    preds: np.ndarray,
    targets: np.ndarray,
    class_names: Optional[List[str]] = None,
    num_classes: Optional[int] = None,
) -> Dict:
    if num_classes is None:
        num_classes = int(targets.max()) + 1

    acc      = accuracy(preds, targets)
    f1_macro = macro_f1(preds, targets)
    f1_wt    = weighted_f1(preds, targets)
    per_cls  = per_class_accuracy(preds, targets, num_classes)
    cm       = confusion_matrix(targets, preds, labels=list(range(num_classes)))

    report = classification_report(
        targets, preds,
        labels=list(range(num_classes)),
        target_names=class_names,
        zero_division=0,
    )

    return {
        "acc":           acc,
        "f1_macro":      f1_macro,
        "f1_weighted":   f1_wt,
        "per_class_acc": per_cls,
        "confusion_matrix": cm,
        "report":        report,
    }


def print_metrics(metrics: Dict, prefix: str = "") -> None:
    tag = f"[{prefix}] " if prefix else ""
    print(f"{tag}Acc: {metrics['acc']:.4f}  "
          f"F1-macro: {metrics['f1_macro']:.4f}  "
          f"F1-weighted: {metrics['f1_weighted']:.4f}")
    print(metrics["report"])
