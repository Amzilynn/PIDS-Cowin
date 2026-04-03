# -*- coding: utf-8 -*-
"""
EfficientNet-B2 Facial Emotion Classifier
==========================================
Loads an EfficientNet-B2 backbone (via timm) with a 7-class emotion head.

Weight loading priority
-----------------------
1. ``checkpoint_path`` arg  -- explicit local .pth / .pt file
2. Default cache: ~/.cache/cowin_models/efficientnet_b2_emotion.pth
3. HuggingFace Hub auto-download (``huggingface_hub`` optional dep)
4. ImageNet-pretrained backbone + untrained head  (fallback, warns)

Emotion labels (FER2013 / AffectNet standard order)
----------------------------------------------------
    0: angry | 1: disgust | 2: fear | 3: happy
    4: sad   | 5: surprise | 6: neutral
"""

from __future__ import annotations

import logging
import os

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMOTIONS: list[str] = [
    "angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"
]

# EfficientNet-B2 native input resolution
_INPUT_SIZE: int = 260

# Local cache directory for downloaded weights
_CACHE_DIR: str = os.path.join(os.path.expanduser("~"), ".cache", "cowin_models")
_DEFAULT_CKPT: str = os.path.join(_CACHE_DIR, "efficientnet_b2_emotion.pth")

# Optional HuggingFace repo containing a FER2013-tuned EfficientNet-B2.
# Set to None to disable auto-download.
_HF_REPO_ID: str | None = "AtmanAI/emotion-detection-efficientnet-b2-v1"
_HF_FILENAME: str = "emotion-detection-efficientnet-b2-v1.pth"

# ImageNet normalisation (standard for timm models)
_IMAGENET_MEAN = [0.485, 0.456, 0.406]
_IMAGENET_STD  = [0.229, 0.224, 0.225]


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class EfficientNetB2EmotionClassifier:
    """
    EfficientNet-B2 based facial emotion recogniser.

    Parameters
    ----------
    device:
        "auto" | "cuda" | "cpu"
    checkpoint_path:
        Path to a local .pth / .pt checkpoint file.
        If None the class tries the default cache, then HuggingFace,
        then falls back to ImageNet weights (with a warning).

    Usage
    -----
    ::

        clf = EfficientNetB2EmotionClassifier()
        scores = clf.predict(face_bgr_crop)   # dict[str, float]
    """

    def __init__(
        self,
        device: str = "auto",
        checkpoint_path: str | None = None,
    ) -> None:
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        logger.info("[EfficientNet-B2] device=%s", self.device)

        self.model: nn.Module = self._build_model(checkpoint_path)
        self.model.eval()

        self._preprocess = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((_INPUT_SIZE, _INPUT_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=_IMAGENET_MEAN, std=_IMAGENET_STD),
        ])

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def predict(self, face_bgr: np.ndarray) -> dict[str, float]:
        """
        Run inference on a single BGR face crop.

        Parameters
        ----------
        face_bgr:
            BGR numpy array of any spatial size -- resized internally to
            260x260 before inference.

        Returns
        -------
        dict[str, float]
            Normalised probabilities for each emotion (sum ~= 1.0).
            Example: {"happy": 0.72, "neutral": 0.18, ...}
        """
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        tensor = self._preprocess(face_rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(tensor)
            probs  = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        return {emotion: float(probs[i]) for i, emotion in enumerate(EMOTIONS)}

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _build_model(self, checkpoint_path: str | None) -> nn.Module:
        """Construct EfficientNet-B2 with a 7-class head and load weights."""
        from torchvision import models

        weights_path = checkpoint_path or self._resolve_weights()
        
        # 1. Build the torchvision architecture
        model = models.efficientnet_b2(weights=None)
        
        # 2. Modify the classifier head to 7 classes instead of 1000
        num_ftrs = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(num_ftrs, len(EMOTIONS))

        if weights_path and os.path.isfile(weights_path):
            logger.info("[EfficientNet-B2] Loading weights from %s", weights_path)
            state = torch.load(weights_path, map_location=self.device)

            # Unwrap common checkpoint wrappers
            for key in ("model_state_dict", "state_dict", "model"):
                if isinstance(state, dict) and key in state:
                    state = state[key]
                    break

            missing, unexpected = model.load_state_dict(state, strict=False)
            if missing:
                logger.warning("[EfficientNet-B2] Missing keys (Torchvision): %s", missing[:5])
            if unexpected:
                logger.warning("[EfficientNet-B2] Unexpected keys (Torchvision): %s", unexpected[:5])

        else:
            # Fallback: ImageNet backbone + randomly initialised head
            logger.warning(
                "[EfficientNet-B2] No fine-tuned checkpoint found. "
                "Falling back to ImageNet-pretrained backbone with an untrained "
                "7-class head. Emotion predictions will be unreliable until the "
                "model is fine-tuned on emotion data (FER2013 / AffectNet)."
            )
            model = models.efficientnet_b2(weights=models.EfficientNet_B2_Weights.DEFAULT)
            model.classifier[1] = nn.Linear(num_ftrs, len(EMOTIONS))

        return model.to(self.device)

    def _resolve_weights(self) -> str | None:
        """
        Return path to a weights file, downloading from HuggingFace if needed.
        Returns None if no checkpoint is available.
        """
        # 1. Default cache location already populated
        if os.path.isfile(_DEFAULT_CKPT):
            return _DEFAULT_CKPT

        # 2. Attempt HuggingFace Hub download
        if _HF_REPO_ID is not None:
            try:
                from huggingface_hub import hf_hub_download  # optional dep

                os.makedirs(_CACHE_DIR, exist_ok=True)
                logger.info(
                    "[EfficientNet-B2] Downloading checkpoint from HuggingFace: %s",
                    _HF_REPO_ID,
                )
                downloaded = hf_hub_download(
                    repo_id=_HF_REPO_ID,
                    filename=_HF_FILENAME,
                    cache_dir=_CACHE_DIR,
                )
                # Copy to our canonical name so we skip downloads next time
                if downloaded and os.path.isfile(downloaded):
                    import shutil
                    shutil.copy2(downloaded, _DEFAULT_CKPT)
                    return _DEFAULT_CKPT
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[EfficientNet-B2] HuggingFace download failed: %s", exc
                )

        return None
