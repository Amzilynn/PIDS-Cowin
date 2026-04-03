"""
Unit tests for the CV behaviour analysis modules.
Run with: pytest dso1/tests/ -v
"""

import numpy as np
import pytest


# ─── Body Language Tests ───────────────────────────────────────────────────

class TestBodyLanguageAnalyzer:
    """Tests for BodyLanguageAnalyzer using synthetic black frames."""

    def test_returns_none_on_blank_frame(self):
        """A plain black frame should return None (no person detected)."""
        from dso1.src.cv.body_language import BodyLanguageAnalyzer
        analyzer = BodyLanguageAnalyzer()
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        result = analyzer.analyze(blank)
        assert result is None
        analyzer.close()

    def test_scores_are_bounded(self):
        """If a result is returned, all scores must be in [0, 1]."""
        from dso1.src.cv.body_language import BodyLanguageAnalyzer, BodyLanguageResult
        # Simulate a valid result directly (unit test without camera)
        result = BodyLanguageResult(
            posture_score=0.8,
            openness_score=0.6,
            fidget_score=0.1,
            lean="neutral",
            overall_score=0.75,
        )
        for attr in ("posture_score", "openness_score", "fidget_score", "overall_score"):
            val = getattr(result, attr)
            assert 0.0 <= val <= 1.0, f"{attr} out of bounds: {val}"

    def test_lean_values(self):
        """Lean must be one of the expected strings."""
        from dso1.src.cv.body_language import BodyLanguageResult
        for lean in ("forward", "neutral", "backward"):
            r = BodyLanguageResult(0.5, 0.5, 0.0, lean, 0.5)
            assert r.lean in ("forward", "neutral", "backward")


# ─── Emotion Result Tests ──────────────────────────────────────────────────

class TestEmotionResult:
    """Tests for EmotionResult dataclass logic."""

    def test_stress_score_bounded(self):
        from dso1.src.cv.face_emotion import EmotionResult
        result = EmotionResult(
            dominant_emotion="fear",
            scores={"fear": 0.6, "angry": 0.3, "happy": 0.1, "neutral": 0.0,
                    "disgust": 0.0, "sad": 0.0, "surprise": 0.0},
            stress_score=0.9,
            confidence_score=0.1,
            eye_contact=False,
        )
        assert 0.0 <= result.stress_score <= 1.0
        assert 0.0 <= result.confidence_score <= 1.0

    def test_dominant_emotion_is_string(self):
        from dso1.src.cv.face_emotion import EmotionResult
        result = EmotionResult(
            dominant_emotion="happy",
            scores={"happy": 0.9, "neutral": 0.1, "fear": 0.0,
                    "angry": 0.0, "disgust": 0.0, "sad": 0.0, "surprise": 0.0},
            stress_score=0.0,
            confidence_score=0.9,
            eye_contact=True,
        )
        assert isinstance(result.dominant_emotion, str)
        assert result.dominant_emotion == "happy"


# ─── Tone Result Tests ─────────────────────────────────────────────────────

class TestToneResult:
    """Tests for ToneResult dataclass."""

    def test_default_values(self):
        from dso1.src.cv.tone_analysis import ToneAnalyzer
        result = ToneAnalyzer._default_result()
        assert result.tone_label == "unknown"
        assert result.overall_score == 0.0

    def test_tone_labels_are_valid(self):
        from dso1.src.cv.tone_analysis import ToneResult
        valid_labels = {"confident", "hesitant", "monotone", "energetic", "stressed", "unknown"}
        for label in valid_labels:
            r = ToneResult(
                pitch_mean=200.0,
                pitch_variance=1000.0,
                energy=0.03,
                speaking_rate=0.1,
                pause_ratio=0.2,
                tone_label=label,
                overall_score=0.7,
            )
            assert r.tone_label in valid_labels


# ─── Fusion Scorer Tests ───────────────────────────────────────────────────

class TestFusionScorer:
    """Tests for FusionScorer."""

    def _make_body(self):
        from dso1.src.cv.body_language import BodyLanguageResult
        return BodyLanguageResult(
            posture_score=0.8, openness_score=0.7,
            fidget_score=0.1, lean="neutral", overall_score=0.75
        )

    def _make_face(self):
        from dso1.src.cv.face_emotion import EmotionResult
        return EmotionResult(
            dominant_emotion="happy",
            scores={"happy": 0.8, "neutral": 0.1, "fear": 0.0,
                    "angry": 0.0, "disgust": 0.0, "sad": 0.05, "surprise": 0.05},
            stress_score=0.05,
            confidence_score=0.9,
            eye_contact=True,
        )

    def _make_tone(self):
        from dso1.src.cv.tone_analysis import ToneResult
        return ToneResult(
            pitch_mean=220.0, pitch_variance=3000.0, energy=0.04,
            speaking_rate=0.12, pause_ratio=0.15,
            tone_label="confident", overall_score=0.82
        )

    def test_fused_scores_in_bounds(self):
        from dso1.src.cv.fusion import FusionScorer
        scorer = FusionScorer()
        snap = scorer.fuse(1000.0, self._make_body(), self._make_face(), self._make_tone())

        for attr in ("stress_score", "confidence_score", "engagement_score", "performance_score"):
            val = getattr(snap, attr)
            assert 0.0 <= val <= 1.0, f"{attr} out of bounds: {val}"

    def test_fuse_with_none_modules(self):
        """Fusion should gracefully handle missing modules."""
        from dso1.src.cv.fusion import FusionScorer
        scorer = FusionScorer()
        snap = scorer.fuse(500.0, None, None, None)
        assert 0.0 <= snap.performance_score <= 1.0

    def test_high_confidence_scenario(self):
        """Confident body + happy face + confident tone → performance > 0.6."""
        from dso1.src.cv.fusion import FusionScorer
        scorer = FusionScorer()
        snap = scorer.fuse(0.0, self._make_body(), self._make_face(), self._make_tone())
        assert snap.performance_score > 0.6, (
            f"Expected performance > 0.6, got {snap.performance_score}"
        )

    def test_weights_must_sum_to_one(self):
        from dso1.src.cv.fusion import FusionScorer
        with pytest.raises(AssertionError):
            FusionScorer(body_weight=0.5, face_weight=0.5, tone_weight=0.5)

    def test_summary_is_string(self):
        from dso1.src.cv.fusion import FusionScorer
        scorer = FusionScorer()
        snap = scorer.fuse(0.0, self._make_body(), self._make_face(), self._make_tone())
        assert isinstance(snap.summary, str)
        assert len(snap.summary) > 0


# ─── Session Logger Tests ──────────────────────────────────────────────────

class TestSessionLogger:
    """Tests for SessionLogger."""

    def _make_snapshot(self, ts=0.0):
        from dso1.src.cv.fusion import FusionScorer
        from dso1.src.cv.body_language import BodyLanguageResult
        from dso1.src.cv.face_emotion import EmotionResult
        from dso1.src.cv.tone_analysis import ToneResult

        body = BodyLanguageResult(0.8, 0.7, 0.1, "neutral", 0.75)
        face = EmotionResult("happy", {"happy": 0.8, "neutral": 0.1, "fear": 0.0,
                                       "angry": 0.0, "disgust": 0.0, "sad": 0.05, "surprise": 0.05},
                             0.05, 0.9, True)
        tone = ToneResult(220.0, 3000.0, 0.04, 0.12, 0.15, "confident", 0.82)
        return FusionScorer().fuse(ts, body, face, tone)

    def test_csv_created(self, tmp_path):
        from dso1.src.cv.session_logger import SessionLogger
        logger = SessionLogger(output_dir=str(tmp_path))
        logger.log(self._make_snapshot(0.0))
        logger.log(self._make_snapshot(1000.0))
        summary = logger.close()
        assert logger.csv_path.exists()

    def test_json_summary_created(self, tmp_path):
        from dso1.src.cv.session_logger import SessionLogger
        logger = SessionLogger(output_dir=str(tmp_path))
        logger.log(self._make_snapshot(0.0))
        logger.log(self._make_snapshot(1000.0))
        summary = logger.close()
        assert logger.json_path.exists()
        assert "grade" in summary
        assert "averages" in summary

    def test_grade_format(self, tmp_path):
        from dso1.src.cv.session_logger import SessionLogger
        logger = SessionLogger(output_dir=str(tmp_path))
        for i in range(5):
            logger.log(self._make_snapshot(float(i * 1000)))
        summary = logger.close()
        assert "—" in summary["grade"]
