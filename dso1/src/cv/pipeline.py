"""
Main entry point — Real-time delegate behaviour analysis.

Runs the full pipeline:
  1. Webcam capture (OpenCV)
  2. Body language analysis (MediaPipe Pose)
  3. Facial emotion recognition (DeepFace / FER)
  4. Tone & voice analysis (PyAudio + librosa) — background thread
  5. Fusion scoring
  6. Live OpenCV overlay

Press Q to quit. Session data is auto-saved via SessionLogger.
"""

import time
import cv2
import numpy as np
from pathlib import Path

from dso1.src.cv import (
    BodyLanguageAnalyzer,
    FaceEmotionAnalyzer,
    ToneAnalyzer,
    FusionScorer,
    SessionSnapshot,
    SessionLogger,
)

# ── Config ────────────────────────────────────────────────────────────────
CAMERA_INDEX   = 0
FRAME_WIDTH    = 1280
FRAME_HEIGHT   = 720
SESSIONS_DIR   = Path("sessions")


def draw_hud(frame: np.ndarray, snap: SessionSnapshot) -> np.ndarray:
    """Render HUD overlay with performance metrics."""
    h, w = frame.shape[:2]

    # Semi-transparent sidebar
    overlay = frame.copy()
    cv2.rectangle(overlay, (w - 280, 0), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    x = w - 265
    y = 30

    def put(text, color=(220, 220, 220), scale=0.58):
        nonlocal y
        cv2.putText(frame, text, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)
        y += 26

    put("── DELEGATE ANALYSIS ──", (100, 200, 255), 0.52)
    y += 6

    put(f"Performance:  {snap.performance_score:.0%}",
        color=_score_color(snap.performance_score))
    put(f"Confidence:   {snap.confidence_score:.0%}",
        color=_score_color(snap.confidence_score))
    put(f"Stress:       {snap.stress_score:.0%}",
        color=_score_color(1.0 - snap.stress_score))
    put(f"Engagement:   {snap.engagement_score:.0%}",
        color=_score_color(snap.engagement_score))

    y += 8
    put("── BODY ──", (180, 180, 180), 0.50)
    if snap.body:
        put(f"Posture:  {snap.body.posture_score:.0%}")
        put(f"Openness: {snap.body.openness_score:.0%}")
        put(f"Fidget:   {snap.body.fidget_score:.0%}")
        put(f"Lean:     {snap.body.lean}")
    else:
        put("No person detected", (100, 100, 255))

    y += 8
    put("── FACE ──", (180, 180, 180), 0.50)
    if snap.face and snap.face.face_detected:
        put(f"Emotion:  {snap.face.dominant_emotion}")
        put(f"Eye cont: {'YES' if snap.face.eye_contact else 'NO'}")
    else:
        put("No face detected", (100, 100, 255))

    y += 8
    put("── VOICE ──", (180, 180, 180), 0.50)
    if snap.tone and snap.tone.tone_label != "unknown":
        put(f"Tone:   {snap.tone.tone_label}")
        put(f"Pauses: {snap.tone.pause_ratio:.0%}")
    else:
        put("Waiting for audio...", (100, 100, 255))

    y += 12
    # Wrap summary text
    words = snap.summary.split()
    line, lines = "", []
    for w_ in words:
        if len(line + w_) > 28:
            lines.append(line.strip())
            line = w_ + " "
        else:
            line += w_ + " "
    if line:
        lines.append(line.strip())

    put("── FEEDBACK ──", (100, 255, 180), 0.50)
    for ln in lines[:4]:
        put(ln, (200, 230, 200), 0.48)

    return frame


def _score_color(score: float) -> tuple:
    """Green = good, yellow = ok, red = bad."""
    if score >= 0.70:
        return (80, 220, 80)
    elif score >= 0.45:
        return (80, 200, 250)
    else:
        return (80, 80, 240)


def main():
    print("[INFO] Initialising modules...")

    body_analyzer  = BodyLanguageAnalyzer()
    face_analyzer  = FaceEmotionAnalyzer(backend="auto", skip_frames=3)
    tone_analyzer  = ToneAnalyzer()
    fusion_scorer  = FusionScorer()
    session_logger = SessionLogger(output_dir=str(SESSIONS_DIR))

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        return

    # Start audio in background thread
    tone_analyzer.start()
    print("[INFO] Pipeline running. Press Q to quit.\n")

    start_time = time.time()


    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Frame capture failed.")
                break

            ts_ms = (time.time() - start_time) * 1000

            # ── Module inference ────────────────────────────────────
            body_result = body_analyzer.analyze(frame)
            face_result = face_analyzer.analyze(frame)
            tone_result = tone_analyzer.get_result()

            # ── Fusion ─────────────────────────────────────────────
            snap = fusion_scorer.fuse(ts_ms, body_result, face_result, tone_result)

            # ── Pose skeleton overlay ───────────────────────────────
            body_analyzer.draw_landmarks(frame)

            # ── Emotion overlay ─────────────────────────────────────
            face_analyzer.draw_overlay(frame, face_result)

            # ── HUD ─────────────────────────────────────────────────
            frame = draw_hud(frame, snap)

            cv2.imshow("Co-Win | Delegate Analysis", frame)

            # ── Log ─────────────────────────────────────────────────
            session_logger.log(snap)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        print("\n[INFO] Shutting down...")
        tone_analyzer.stop()
        body_analyzer.close()
        face_analyzer.close()
        cap.release()
        cv2.destroyAllWindows()
        summary = session_logger.close()
        print(f"\n[INFO] Session Grade: {summary.get('grade', 'N/A')}")


if __name__ == "__main__":
    main()
