"""
Unit tests for EfficientNetB2EmotionClassifier.

These tests run without a camera or fine-tuned weights — they validate the
model architecture, input handling, and output contract using a random tensor.
"""

import numpy as np
import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def classifier():
    """Instantiate EfficientNetB2EmotionClassifier once for the whole module."""
    pytest.importorskip("timm",  reason="timm not installed — skipping EfficientNet tests")
    pytest.importorskip("torch", reason="torch not installed — skipping EfficientNet tests")

    from dso1.src.cv.efficientnet_emotion import EfficientNetB2EmotionClassifier
    # CPU + no external checkpoint needed for structural tests
    return EfficientNetB2EmotionClassifier(device="cpu", checkpoint_path=None)


@pytest.fixture
def dummy_face_bgr() -> np.ndarray:
    """Random 120×100 BGR face crop (simulates a real detection crop)."""
    rng = np.random.default_rng(42)
    return (rng.integers(0, 256, (120, 100, 3), dtype=np.uint8))


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestEfficientNetB2EmotionClassifier:
    """Structural and contract tests — no camera, no fine-tuned weights."""

    def test_model_loads(self, classifier):
        """Model should initialise without raising."""
        import torch.nn as nn
        assert isinstance(classifier.model, nn.Module)

    def test_predict_returns_dict(self, classifier, dummy_face_bgr):
        """predict() should return a dict."""
        result = classifier.predict(dummy_face_bgr)
        assert isinstance(result, dict)

    def test_predict_all_emotions_present(self, classifier, dummy_face_bgr):
        """All seven FER emotion keys must be present."""
        from dso1.src.cv.efficientnet_emotion import EMOTIONS
        result = classifier.predict(dummy_face_bgr)
        assert set(result.keys()) == set(EMOTIONS)

    def test_probabilities_sum_to_one(self, classifier, dummy_face_bgr):
        """Softmax output must sum to ~1.0."""
        result = classifier.predict(dummy_face_bgr)
        total = sum(result.values())
        assert abs(total - 1.0) < 1e-4, f"Probabilities sum to {total}"

    def test_probabilities_non_negative(self, classifier, dummy_face_bgr):
        """All probabilities must be non-negative."""
        result = classifier.predict(dummy_face_bgr)
        for emotion, prob in result.items():
            assert prob >= 0.0, f"{emotion} probability is negative: {prob}"

    @pytest.mark.parametrize("h,w", [
        (48,  48),    # very small
        (128, 96),    # landscape crop
        (260, 260),   # native resolution
        (400, 300),   # larger than native
    ])
    def test_arbitrary_input_sizes(self, classifier, h, w):
        """Model should handle any BGR crop size (resized internally)."""
        rng = np.random.default_rng(0)
        face = rng.integers(0, 256, (h, w, 3), dtype=np.uint8)
        result = classifier.predict(face)
        assert isinstance(result, dict)
        assert abs(sum(result.values()) - 1.0) < 1e-4
