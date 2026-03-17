"""
src/utils/seed.py
──────────────────
Set all random seeds for full reproducibility across CPU, GPU, cuDNN.
"""

import os
import random
import numpy as np
import torch


def seed_everything(seed: int = 42) -> None:
    """Seed Python, NumPy, PyTorch (CPU + all GPUs) and cuDNN."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # Deterministic convolutions — may slow training slightly
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    print(f"[seed] All seeds set to {seed}")
