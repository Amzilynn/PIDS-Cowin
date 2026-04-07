"""
Session Logger
Saves per-frame snapshots to CSV and generates a summary JSON
at the end of a session.
"""

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path

from dso1.src.cv.fusion import SessionSnapshot


class SessionLogger:
    """
    Writes every SessionSnapshot to a CSV (row per frame) and
    builds a JSON summary on close().

    Usage:
        logger = SessionLogger(output_dir="sessions/")
        logger.log(snapshot)
        ...
        logger.close()
    """

    CSV_FIELDS = [
        "timestamp_ms",
        "performance_score",
        "confidence_score",
        "stress_score",
        "engagement_score",
        # body
        "posture_score",
        "openness_score",
        "fidget_score",
        "lean",
        # face
        "dominant_emotion",
        "face_stress",
        "face_confidence",
        "eye_contact",
        # tone
        "tone_label",
        "pitch_mean",
        "pitch_variance",
        "energy",
        "speaking_rate",
        "pause_ratio",
        "tone_overall",
    ]

    def __init__(self, output_dir: str = "sessions"):
        self._dir      = Path(output_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

        session_id    = time.strftime("%Y%m%d_%H%M%S")
        self._csv_path  = self._dir / f"session_{session_id}.csv"
        self._json_path = self._dir / f"session_{session_id}_summary.json"

        self.conversation_history = []  # List of {"role": x, "text": y, "timestamp": z}

        self._file   = self._csv_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.CSV_FIELDS)
        self._writer.writeheader()

        self._rows: list[dict] = []

    # ── Public API ────────────────────────────────────────────────────────

    def log(self, snap: SessionSnapshot) -> None:
        """Write a single snapshot row to the CSV."""
        row = self._flatten(snap)
        self._writer.writerow(row)
        self._rows.append(row)

    def log_conversation(self, role: str, text: str) -> None:
        """Record an interaction in the transcript."""
        self.conversation_history.append({
            "role": role,
            "text": text,
            "timestamp_ms": self._rows[-1]["timestamp_ms"] if self._rows else 0
        })

    def close(self) -> dict:
        """
        Flush CSV, generate JSON summary, and return summary dict.
        """
        self._file.close()

        summary = self._build_summary()
        with self._json_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"[SessionLogger] CSV  → {self._csv_path}")
        print(f"[SessionLogger] JSON → {self._json_path}")
        return summary

    @property
    def csv_path(self) -> Path:
        return self._csv_path

    @property
    def json_path(self) -> Path:
        return self._json_path

    # ── Private ───────────────────────────────────────────────────────────

    def _flatten(self, snap: SessionSnapshot) -> dict:
        row: dict = {
            "timestamp_ms":       snap.timestamp_ms,
            "performance_score":  snap.performance_score,
            "confidence_score":   snap.confidence_score,
            "stress_score":       snap.stress_score,
            "engagement_score":   snap.engagement_score,
        }

        # Body
        b = snap.body
        row.update({
            "posture_score":  b.posture_score  if b else "",
            "openness_score": b.openness_score if b else "",
            "fidget_score":   b.fidget_score   if b else "",
            "lean":           b.lean           if b else "",
        })

        # Face
        f = snap.face
        row.update({
            "dominant_emotion": f.dominant_emotion  if f else "",
            "face_stress":      f.stress_score       if f else "",
            "face_confidence":  f.confidence_score   if f else "",
            "eye_contact":      f.eye_contact         if f else "",
        })

        # Tone
        t = snap.tone
        row.update({
            "tone_label":    t.tone_label    if t else "",
            "pitch_mean":    t.pitch_mean    if t else "",
            "pitch_variance":t.pitch_variance if t else "",
            "energy":        t.energy        if t else "",
            "speaking_rate": t.speaking_rate if t else "",
            "pause_ratio":   t.pause_ratio   if t else "",
            "tone_overall":  t.overall_score if t else "",
        })

        return row

    def _build_summary(self) -> dict:
        if not self._rows:
            return {"error": "No data recorded."}

        def avg(key: str) -> float:
            vals = [r[key] for r in self._rows if r.get(key) not in ("", None)]
            return round(sum(vals) / len(vals), 3) if vals else 0.0

        def most_common(key: str) -> str:
            vals = [r[key] for r in self._rows if r.get(key) not in ("", None)]
            return max(set(vals), key=vals.count) if vals else "unknown"

        # Eye contact rate
        ec_vals = [r["eye_contact"] for r in self._rows if r.get("eye_contact") not in ("", None)]
        eye_contact_rate = round(
            sum(1 for v in ec_vals if v in (True, "True")) / len(ec_vals), 3
        ) if ec_vals else 0.0

        duration_s = (self._rows[-1]["timestamp_ms"] - self._rows[0]["timestamp_ms"]) / 1000

        return {
            "session_duration_s": round(duration_s, 1),
            "total_frames":       len(self._rows),
            "averages": {
                "performance":  avg("performance_score"),
                "confidence":   avg("confidence_score"),
                "stress":       avg("stress_score"),
                "engagement":   avg("engagement_score"),
                "posture":      avg("posture_score"),
                "openness":     avg("openness_score"),
                "fidget":       avg("fidget_score"),
                "pause_ratio":  avg("pause_ratio"),
            },
            "dominant_emotion":   most_common("dominant_emotion"),
            "dominant_tone":      most_common("tone_label"),
            "eye_contact_rate":   eye_contact_rate,
            "grade": self._grade(avg("performance_score")),
            "conversation_history": self.conversation_history,
        }

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 0.85: return "A — Excellent"
        if score >= 0.70: return "B — Good"
        if score >= 0.55: return "C — Satisfactory"
        if score >= 0.40: return "D — Needs Improvement"
        return "F — Poor"
