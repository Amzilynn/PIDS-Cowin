"""
Body Language Analyzer
Detects posture, gestures, and fidgeting using MediaPipe Pose.
"""

import cv2
import mediapipe as mp
import numpy as np
from dataclasses import dataclass


@dataclass
class BodyLanguageResult:
    posture_score: float        # 0.0 (slouched) → 1.0 (upright)
    openness_score: float       # 0.0 (closed/crossed) → 1.0 (open)
    fidget_score: float         # 0.0 (calm) → 1.0 (very fidgety)
    lean: str                   # "forward", "neutral", "backward"
    overall_score: float        # Weighted composite of the above


class BodyLanguageAnalyzer:
    """
    Analyzes body language from video frames using MediaPipe Pose.
    Runs on CPU — no GPU required.
    """

    def __init__(self, fidget_window: int = 15):
        """
        Args:
            fidget_window: Number of frames to use for fidget detection.
        """
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,          # 0=lite, 1=full, 2=heavy
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.mp_draw = mp.solutions.drawing_utils

        # History for fidget detection
        self._fidget_window = fidget_window
        self._landmark_history: list[np.ndarray] = []

    def analyze(self, frame_bgr: np.ndarray) -> BodyLanguageResult | None:
        """
        Analyze a single BGR frame.

        Returns:
            BodyLanguageResult or None if no person is detected.
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)

        if not result.pose_landmarks:
            return None

        lm = result.pose_landmarks.landmark

        posture  = self._compute_posture(lm)
        openness = self._compute_openness(lm)
        fidget   = self._compute_fidget(lm)
        lean     = self._compute_lean(lm)

        overall = (
            0.40 * posture +
            0.30 * openness +
            0.30 * (1.0 - fidget)   # less fidgeting = higher score
        )

        return BodyLanguageResult(
            posture_score=round(posture, 3),
            openness_score=round(openness, 3),
            fidget_score=round(fidget, 3),
            lean=lean,
            overall_score=round(overall, 3),
        )

    def draw_landmarks(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Overlay pose landmarks on the frame (for debug / dashboard)."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        if result.pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame_bgr,
                result.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
            )
        return frame_bgr

    # ─── Private helpers ───────────────────────────────────────────────────

    def _compute_posture(self, lm) -> float:
        """
        Measures vertical alignment of shoulders vs. hips.
        Score = 1.0 when perfectly upright.
        """
        LEFT_SHOULDER  = self.mp_pose.PoseLandmark.LEFT_SHOULDER
        RIGHT_SHOULDER = self.mp_pose.PoseLandmark.RIGHT_SHOULDER
        LEFT_HIP       = self.mp_pose.PoseLandmark.LEFT_HIP
        RIGHT_HIP      = self.mp_pose.PoseLandmark.RIGHT_HIP

        sh_y = (lm[LEFT_SHOULDER].y + lm[RIGHT_SHOULDER].y) / 2
        hp_y = (lm[LEFT_HIP].y + lm[RIGHT_HIP].y) / 2

        # Normalized distance. Larger vertical gap = more upright.
        gap = hp_y - sh_y
        score = np.clip(gap / 0.35, 0.0, 1.0)   # 0.35 = calibrated threshold
        return float(score)

    def _compute_openness(self, lm) -> float:
        """
        Measures arm openness.
        Crossed arms (wrists near center) → low score.
        Open arms (wrists wide) → high score.
        """
        LEFT_WRIST  = self.mp_pose.PoseLandmark.LEFT_WRIST
        RIGHT_WRIST = self.mp_pose.PoseLandmark.RIGHT_WRIST
        LEFT_HIP    = self.mp_pose.PoseLandmark.LEFT_HIP
        RIGHT_HIP   = self.mp_pose.PoseLandmark.RIGHT_HIP

        wrist_dist = abs(lm[LEFT_WRIST].x - lm[RIGHT_WRIST].x)
        hip_dist   = abs(lm[LEFT_HIP].x - lm[RIGHT_HIP].x)

        if hip_dist < 1e-5:
            return 0.5

        ratio = wrist_dist / (hip_dist + 1e-5)
        score = np.clip((ratio - 0.5) / 1.5, 0.0, 1.0)
        return float(score)

    def _compute_fidget(self, lm) -> float:
        """
        Estimates fidgeting by measuring average landmark displacement
        over a sliding window of frames.
        """
        pts = np.array([[l.x, l.y] for l in lm], dtype=np.float32)
        self._landmark_history.append(pts)

        if len(self._landmark_history) > self._fidget_window:
            self._landmark_history.pop(0)

        if len(self._landmark_history) < 2:
            return 0.0

        diffs = [
            np.mean(np.abs(self._landmark_history[i] - self._landmark_history[i - 1]))
            for i in range(1, len(self._landmark_history))
        ]
        motion = float(np.mean(diffs))
        score  = np.clip(motion / 0.02, 0.0, 1.0)   # 0.02 = calibrated threshold
        return float(score)

    def _compute_lean(self, lm) -> str:
        """
        Detects forward / neutral / backward lean via nose-shoulder relationship.
        """
        NOSE           = self.mp_pose.PoseLandmark.NOSE
        LEFT_SHOULDER  = self.mp_pose.PoseLandmark.LEFT_SHOULDER
        RIGHT_SHOULDER = self.mp_pose.PoseLandmark.RIGHT_SHOULDER

        nose_x = lm[NOSE].x
        sh_x   = (lm[LEFT_SHOULDER].x + lm[RIGHT_SHOULDER].x) / 2
        diff   = nose_x - sh_x

        if diff > 0.05:
            return "forward"
        elif diff < -0.05:
            return "backward"
        return "neutral"

    def close(self):
        self.pose.close()
