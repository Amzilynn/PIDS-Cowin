"""
Facial Emotion Recognition
Detects face landmarks and classifies emotions using DeepFace.
"""

import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass, field

try:
    from deepface import DeepFace
    _DEEPFACE_AVAILABLE = True
except ImportError:
    _DEEPFACE_AVAILABLE = False

try:
    from fer import FER
    _FER_AVAILABLE = True
except ImportError:
    _FER_AVAILABLE = False


EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]


@dataclass
class EmotionResult:
    dominant_emotion: str
    scores: dict[str, float]          # e.g. {"happy": 0.82, "fear": 0.05, ...}
    stress_score: float                # Derived: fear + angry + disgust
    confidence_score: float            # Derived: happy + neutral
    eye_contact: bool                  # True if gaze is directed forward
    face_detected: bool = True


class FaceEmotionAnalyzer:
    """
    Detects facial landmarks and classifies emotions from video frames.

    Backend priority:
        1. DeepFace (most accurate, ~300ms on GPU)
        2. FER     (faster, slightly less accurate)
        Raises ImportError if neither is installed.
    """

    def __init__(self, backend: str = "auto", skip_frames: int = 3):
        """
        Args:
            backend:     "deepface" | "fer" | "auto"
            skip_frames: Run emotion model every N frames (performance tweak).
        """
        self._skip_frames = skip_frames
        self._frame_count = 0
        self._last_result: EmotionResult | None = None

        # MediaPipe for face mesh + iris (eye contact)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,    # enables iris landmarks
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # Choose emotion backend
        if backend == "auto":
            if _DEEPFACE_AVAILABLE:
                backend = "deepface"
            elif _FER_AVAILABLE:
                backend = "fer"
            else:
                raise ImportError(
                    "Install either 'deepface' or 'fer':\n"
                    "  pip install deepface\n"
                    "  pip install fer"
                )

        self._backend = backend
        if backend == "fer":
            self._fer = FER(mtcnn=True)

    def analyze(self, frame_bgr: np.ndarray) -> EmotionResult:
        """
        Analyze a single BGR frame.
        Returns cached result on skipped frames for performance.
        """
        self._frame_count += 1

        # Run model every N frames
        if (self._frame_count % self._skip_frames == 0
                or self._last_result is None):
            result = self._run_emotion_model(frame_bgr)
            eye_contact = self._detect_eye_contact(frame_bgr)

            if result is None:
                self._last_result = EmotionResult(
                    dominant_emotion="neutral",
                    scores={e: 0.0 for e in EMOTIONS},
                    stress_score=0.0,
                    confidence_score=0.5,
                    eye_contact=eye_contact,
                    face_detected=False,
                )
            else:
                scores = result
                dominant = max(scores, key=scores.get)
                stress = scores.get("fear", 0) + scores.get("angry", 0) + scores.get("disgust", 0)
                confidence = scores.get("happy", 0) + scores.get("neutral", 0)

                self._last_result = EmotionResult(
                    dominant_emotion=dominant,
                    scores=scores,
                    stress_score=round(min(stress, 1.0), 3),
                    confidence_score=round(min(confidence, 1.0), 3),
                    eye_contact=eye_contact,
                    face_detected=True,
                )

        return self._last_result

    def draw_overlay(self, frame_bgr: np.ndarray, result: EmotionResult) -> np.ndarray:
        """Draw emotion label and scores on frame."""
        if not result.face_detected:
            cv2.putText(frame_bgr, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            return frame_bgr

        label = f"Emotion: {result.dominant_emotion.upper()}"
        stress_bar = f"Stress: {result.stress_score:.0%}"
        conf_bar   = f"Confidence: {result.confidence_score:.0%}"
        eye_label  = "Eye Contact: YES" if result.eye_contact else "Eye Contact: NO"

        y = 30
        for text, color in [
            (label,     (255, 255, 255)),
            (stress_bar,(0, 80, 255)),
            (conf_bar,  (0, 200, 80)),
            (eye_label, (200, 200, 0)),
        ]:
            cv2.putText(frame_bgr, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
            y += 28

        return frame_bgr

    # ─── Private helpers ───────────────────────────────────────────────────

    def _run_emotion_model(self, frame_bgr: np.ndarray) -> dict[str, float] | None:
        """Run whichever backend is available. Returns normalized score dict."""
        try:
            if self._backend == "deepface":
                analysis = DeepFace.analyze(
                    frame_bgr,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )
                raw = analysis[0]["emotion"]
                total = sum(raw.values()) or 1.0
                return {k.lower(): v / total for k, v in raw.items()}

            elif self._backend == "fer":
                detected = self._fer.detect_emotions(frame_bgr)
                if not detected:
                    return None
                raw = detected[0]["emotions"]
                total = sum(raw.values()) or 1.0
                return {k: v / total for k, v in raw.items()}

        except Exception:
            return None

        return None

    def _detect_eye_contact(self, frame_bgr: np.ndarray) -> bool:
        """
        Approximate eye contact detection using MediaPipe Iris landmarks.
        Returns True if both irises are reasonably centered (looking forward).
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.face_mesh.process(rgb)

        if not result.multi_face_landmarks:
            return False

        lm = result.multi_face_landmarks[0].landmark

        # MediaPipe FaceMesh iris indices (left: 468-471, right: 473-476)
        LEFT_IRIS_CENTER  = 468
        RIGHT_IRIS_CENTER = 473
        LEFT_EYE_INNER    = 133   # inner corner left eye
        RIGHT_EYE_INNER   = 362  # inner corner right eye

        try:
            li = lm[LEFT_IRIS_CENTER]
            ri = lm[RIGHT_IRIS_CENTER]
            le_inner = lm[LEFT_EYE_INNER]
            re_inner = lm[RIGHT_EYE_INNER]

            # Check if irises are near the center of each eye
            left_offset  = abs(li.x - le_inner.x)
            right_offset = abs(ri.x - re_inner.x)

            return left_offset < 0.04 and right_offset < 0.04
        except IndexError:
            return False

    def close(self):
        self.face_mesh.close()
