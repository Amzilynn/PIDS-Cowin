"""
Fusion Scorer
Combines body language, facial emotion, and tone signals
into a single composite "Delegate Performance Score".
"""

from dataclasses import dataclass
from .body_language import BodyLanguageResult
from .face_emotion import EmotionResult
from .tone_analysis import ToneResult


@dataclass
class SessionSnapshot:
    """A single moment-in-time snapshot of all signals."""
    timestamp_ms: float

    # Raw module results
    body: BodyLanguageResult | None
    face: EmotionResult | None
    tone: ToneResult | None

    # Fused scores (0.0 – 1.0)
    stress_score: float
    confidence_score: float
    engagement_score: float
    performance_score: float    # Overall composite

    # Human-readable summary
    summary: str


class FusionScorer:
    """
    Fuses outputs from all three CV modules into a single
    unified performance assessment.

    Weights (tunable):
        body_language  → 30%
        face_emotion   → 35%
        tone           → 35%
    """

    def __init__(self):
        # Static weights are removed in favor of dynamic cross-modal attention
        pass

    def fuse(
        self,
        timestamp_ms: float,
        body: BodyLanguageResult | None,
        face: EmotionResult | None,
        tone: ToneResult | None,
    ) -> SessionSnapshot:
        """
        Produce a fused SessionSnapshot from module outputs.
        Gracefully handles missing modules (None values).
        """
        # ── Extract individual scores ───────────────────────
        body_score    = body.overall_score    if body else 0.5
        face_conf     = face.confidence_score if face else 0.5
        face_stress   = face.stress_score     if face else 0.0
        tone_score    = tone.overall_score    if tone else 0.5
        tone_stress   = (1.0 - tone_score)    if tone else 0.0

        # ── Dynamic Cross-Modal Attention ───────────────────
        import math
        body_conf = 0.8 if body else 0.1
        face_conf = face.confidence_score if face and face.face_detected else 0.1
        # Tone confidence uses the distilHuBERT confidence score
        tone_conf = getattr(tone, "speech_emotion_conf", 0.0) if tone else 0.1
        if tone_conf <= 0.0:
             tone_conf = 0.5 if tone and tone.energy > 0.01 else 0.1

        # Temperature-scaled Softmax to assign weights dynamically
        # Sharpen the distribution so high quality signals dominate
        temp = 3.0 
        exp_confs = [math.exp(body_conf * temp), math.exp(face_conf * temp), math.exp(tone_conf * temp)]
        sum_exp = sum(exp_confs)
        bw, fw, tw = [e / sum_exp for e in exp_confs]

        # ── Derived composite scores ────────────────────────
        # Weight the stress score dynamically based on face/tone attention
        stress_denom = fw + tw if (fw + tw) > 0 else 1.0
        stress_score = round(
            ((fw / stress_denom) * face_stress) + ((tw / stress_denom) * tone_stress), 3
        )

        confidence_score = round(
            bw * body_score +
            fw * face_conf +
            tw * tone_score,
            3,
        )
        engagement_score = round(
            0.4 * (1.0 - (face.scores.get("neutral", 1.0) if face else 1.0)) +
            0.3 * (body.openness_score if body else 0.5) +
            0.3 * (tone.energy * 10 if tone else 0.5),   # scale energy to 0–1 range
            3,
        )
        engagement_score = min(engagement_score, 1.0)

        performance_score = round(
            0.35 * confidence_score +
            0.35 * (1.0 - stress_score) +
            0.30 * engagement_score,
            3,
        )

        summary = self._build_summary(
            body, face, tone, stress_score, confidence_score, tone_score
        )

        return SessionSnapshot(
            timestamp_ms=timestamp_ms,
            body=body,
            face=face,
            tone=tone,
            stress_score=stress_score,
            confidence_score=confidence_score,
            engagement_score=engagement_score,
            performance_score=performance_score,
            summary=summary,
        )

    # ─── Private ───────────────────────────────────────────────────────────

    @staticmethod
    def _build_summary(
        body: BodyLanguageResult | None,
        face: EmotionResult | None,
        tone: ToneResult | None,
        stress: float,
        confidence: float,
        tone_score: float,
    ) -> str:
        parts = []

        if body:
            if body.posture_score < 0.4:
                parts.append("Slouched posture detected.")
            if body.openness_score < 0.3:
                parts.append("Closed/crossed arms — signals defensiveness.")
            if body.fidget_score > 0.6:
                parts.append("High fidgeting — possible nervousness.")
            if body.lean == "backward":
                parts.append("Leaning backward — may signal withdrawal.")

        if face:
            if stress > 0.5:
                parts.append(f"High stress detected ({face.dominant_emotion}).")
            if not face.eye_contact:
                parts.append("Lack of eye contact.")
            if face.dominant_emotion == "contempt":
                parts.append("Contempt expression — avoid dismissive gestures.")

        if tone:
            if tone.tone_label == "monotone":
                parts.append("Monotone voice — vary pitch to engage better.")
            elif tone.tone_label == "hesitant":
                parts.append("Hesitant delivery — reduce pauses, speak with confidence.")
            elif tone.tone_label == "stressed":
                parts.append("Stressed speech — slow down.")
            if tone.pause_ratio > 0.5:
                parts.append("Too many pauses — practice fluency.")

        if not parts:
            if confidence > 0.75:
                return "Excellent performance! Confident, engaging, and clear delivery."
            elif confidence > 0.5:
                return "Good performance. Minor improvements possible."
            else:
                return "Needs improvement — review posture, expression, and vocal delivery."

        return " ".join(parts)
