# -*- coding: utf-8 -*-
"""
EfficientNet-B2 Facial Emotion Classifier (via hsemotion)
=========================================================
Loads an EfficientNet-B2 backbone natively from the `hsemotion` library.
This resolves previous issues with misaligned checkpoints by using a robust,
fully trained model on AffectNet.

Emotion labels (8 classes)
---------------------------
    0: Anger | 1: Contempt | 2: Disgust | 3: Fear
    4: Happiness | 5: Neutral | 6: Sadness | 7: Surprise
"""

from __future__ import annotations

import logging
import cv2
import numpy as np

try:
    from hsemotion.facial_emotions import HSEmotionRecognizer
    _HSEMOTION_AVAILABLE = True
except ImportError:
    _HSEMOTION_AVAILABLE = False

logger = logging.getLogger(__name__)

# EMOTIONS must match the exact indexing of `enet_b2_8`
EMOTIONS: list[str] = [
    "angry", "contempt", "disgust", "fear", "happy", "neutral", "sad", "surprise"
]


class EfficientNetB2EmotionClassifier:
    """
    EfficientNet-B2 based facial emotion recogniser using hsemotion.

    Parameters
    ----------
    device:
        "auto" | "cuda" | "cpu"
    """

    def __init__(
        self,
        device: str = "auto",
        checkpoint_path: str | None = None, # Left in for signature compatibility, ignored
    ) -> None:
        if not _HSEMOTION_AVAILABLE:
            raise ImportError(
                "hsemotion library is required. Please install it:\n"
                "  pip install hsemotion"
            )

        # Fix for PyTorch 2.6+: hsemotion uses torch.load() without weights_only=False
        # which breaks on models containing custom timm layers like Conv2dSame.
        # It also fails to map CUDA weights to CPU correctly.
        import torch
        _orig_torch_load = torch.load
        def _patched_load(*args, **kwargs):
            kwargs['weights_only'] = False
            # Force map_location so CUDA weights don't crash CPU machines
            if 'map_location' not in kwargs:
                kwargs['map_location'] = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            return _orig_torch_load(*args, **kwargs)
        
        torch.load = _patched_load
        
        try:
            if device == "auto":
                self.device_str = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                self.device_str = device

            logger.info("[EfficientNet-B2] Initializing hsemotion (device=%s)", self.device_str)

            # Initialize the underlying HSEmotionRecognizer natively
            self.model = HSEmotionRecognizer(model_name='enet_b2_8', device=self.device_str)
        finally:
            # Restore original torch.load
            torch.load = _orig_torch_load

    def predict(self, face_bgr: np.ndarray) -> dict[str, float]:
        """
        Run inference on a single BGR face crop.

        Parameters
        ----------
        face_bgr:
            BGR numpy array of any spatial size -- `hsemotion` resizes internally

        Returns
        -------
        dict[str, float]
            Normalised probabilities for each emotion.
            Example: {"happy": 0.72, "neutral": 0.18, "contempt": 0.05...}
        """
        # Convert BGR to RGB as hsemotion expects standard RGB OpenCV arrays
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)

        try:
            # logits=False ensures it passes through a softmax layer
            emotion_label, scores = self.model.predict_emotions(face_rgb, logits=False)
            
            # Map the returned scores to our standardized lowercase dictionary keys
            # Even if hsemotion's internal labels differ slightly in string format, 
            # the ordering for an 8-class model is generally:
            # Anger, Contempt, Disgust, Fear, Happiness, Neutral, Sadness, Surprise
            return {EMOTIONS[i]: float(scores[i]) for i in range(len(EMOTIONS))}
            
        except Exception as e:
            logger.warning("[EfficientNet-B2] Inference failed: %s", e)
            # Return neutral fallback
            fallback = {e: 0.0 for e in EMOTIONS}
            fallback["neutral"] = 1.0
            return fallback

