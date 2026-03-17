"""
src/infer/webcam_infer.py
──────────────────────────
Real-time multimodal emotion + stress inference from webcam or video file.

Pipeline per frame
──────────────────
  1. MediaPipe Face Detection     → face bounding box
  2. MediaPipe Pose               → 33 × 4 keypoints → rolling buffer
  3. FaceEmotionModel             → face features + emotion probabilities
  4. PoseModel (rolling buffer)   → pose features
  5. FusionModel                  → final emotion logits
  6. OpenCV overlay               → face bbox, pose skeleton, prob bar chart

    python src/infer/webcam_infer.py --config configs/inference.yaml
"""

import argparse
import collections
import sys
from pathlib import Path
from typing import Deque, List, Optional

import cv2
import mediapipe as mp
import numpy as np
import torch
import torch.nn.functional as F
from torch.cuda.amp import autocast

import albumentations as A
from albumentations.pytorch import ToTensorV2

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models.face_model import FaceEmotionModel
from src.models.pose_model import PoseModel
from src.models.fusion_model import FusionModel
from src.utils.io import load_yaml

# ── MediaPipe handles ─────────────────────────────────────────────────────────
mp_face = mp.solutions.face_detection
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
mp_draw_styles = mp.solutions.drawing_styles

# ── Colour palette per emotion ────────────────────────────────────────────────
EMOTION_COLORS = {
    "neutral":    (180, 180, 180),
    "happy":      (0,   220,  50),
    "sad":        (200,  80,  80),
    "angry":      (0,    0,  255),
    "fearful":    (160,   0, 200),
    "disgusted":  (0,   160, 120),
    "surprised":  (0,   200, 220),
}
DEFAULT_COLOR = (100, 100, 255)


# ── Image pre-processing for face model ───────────────────────────────────────

def make_face_transform(img_size: int) -> A.Compose:
    return A.Compose([
        A.Resize(img_size, img_size),
        A.Normalize(mean=(0.485, 0.456, 0.406),
                    std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ])


# ── Overlay helpers ───────────────────────────────────────────────────────────

def draw_bar_chart(
    frame: np.ndarray,
    probs: np.ndarray,
    class_names: List[str],
    x0: int = 10,
    y0: int = 10,
    bar_h: int = 18,
    bar_max_w: int = 160,
    gap: int = 4,
) -> None:
    """Draw a vertical probability bar chart in the top-left corner."""
    for i, (name, prob) in enumerate(zip(class_names, probs)):
        y = y0 + i * (bar_h + gap)
        color = EMOTION_COLORS.get(name, DEFAULT_COLOR)
        w = max(1, int(prob * bar_max_w))

        # Background
        cv2.rectangle(frame, (x0, y), (x0 + bar_max_w, y + bar_h),
                      (40, 40, 40), -1)
        # Bar
        cv2.rectangle(frame, (x0, y), (x0 + w, y + bar_h), color, -1)
        # Label
        label = f"{name[:8]:8s} {prob * 100:5.1f}%"
        cv2.putText(frame, label, (x0 + bar_max_w + 6, y + bar_h - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1,
                    cv2.LINE_AA)


def draw_top_emotion(
    frame: np.ndarray,
    emotion: str,
    prob: float,
    x: int,
    y: int,
    font_scale: float = 0.7,
) -> None:
    color = EMOTION_COLORS.get(emotion, DEFAULT_COLOR)
    label = f"{emotion.upper()} {prob * 100:.0f}%"
    cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_DUPLEX,
                font_scale, color, 2, cv2.LINE_AA)


# ── Temporal smoother ─────────────────────────────────────────────────────────

class TemporalSmoother:
    """Running average of probability vectors over N frames."""

    def __init__(self, window: int, num_classes: int) -> None:
        self.buf: Deque[np.ndarray] = collections.deque(maxlen=window)
        self.num_classes = num_classes

    def update(self, probs: np.ndarray) -> np.ndarray:
        self.buf.append(probs)
        return np.mean(self.buf, axis=0)


# ── Pose ring buffer ──────────────────────────────────────────────────────────

class PoseBuffer:
    """Maintains a rolling window of pose keypoint frames."""

    def __init__(self, seq_len: int, input_size: int = 132) -> None:
        self.seq_len    = seq_len
        self.input_size = input_size
        self.buf: Deque[np.ndarray] = collections.deque(
            maxlen=seq_len,
            iterable=[np.zeros(input_size, dtype=np.float32)] * seq_len,
        )

    def push(self, landmarks) -> None:
        """Push one MediaPipe NormalizedLandmarkList frame."""
        if landmarks is None:
            frame = np.zeros(self.input_size, dtype=np.float32)
        else:
            frame = np.array(
                [[lm.x, lm.y, lm.z, lm.visibility]
                 for lm in landmarks.landmark],
                dtype=np.float32,
            ).flatten()
        self.buf.append(frame)

    def get_tensor(self, device: str) -> torch.Tensor:
        arr = np.array(self.buf, dtype=np.float32)   # (seq_len, 132)
        return torch.from_numpy(arr).unsqueeze(0).to(device)  # (1, T, 132)


# ── Main inference class ──────────────────────────────────────────────────────

class MultimodalInference:

    def __init__(self, cfg_path: str) -> None:
        self.cfg = load_yaml(cfg_path)
        self.device = self.cfg.get("device", "cuda")
        if self.device == "cuda" and not torch.cuda.is_available():
            print("[WARNING] CUDA not available, falling back to CPU")
            self.device = "cpu"

        self.class_names: List[str] = self.cfg["classes"]
        self.num_classes = len(self.class_names)
        self.threshold   = self.cfg.get("emotion_threshold", 0.35)
        self.use_amp     = self.cfg.get("amp", True) and self.device == "cuda"
        self.font_scale  = self.cfg["overlay"].get("font_scale", 0.7)

        # ── Load models ───────────────────────────────────────────────────────
        print("Loading face model …")
        face_cfg = load_yaml(str(Path(cfg_path).parent / "face.yaml"))
        self.face_model = FaceEmotionModel.load_checkpoint(
            self.cfg["face_ckpt"], face_cfg, mode="encoder",
            device=self.device)

        # Separate classifier head for single-model emotion (no fusion fallback)
        self.face_classifier = FaceEmotionModel.load_checkpoint(
            self.cfg["face_ckpt"], face_cfg, mode="classifier",
            device=self.device)

        print("Loading pose model …")
        pose_cfg = load_yaml(str(Path(cfg_path).parent / "pose.yaml"))
        self.pose_model = PoseModel.load_checkpoint(
            self.cfg["pose_ckpt"], pose_cfg, mode="encoder",
            device=self.device)

        fusion_ckpt = self.cfg.get("fusion_ckpt")
        self.fusion_model: Optional[FusionModel] = None
        if fusion_ckpt and Path(fusion_ckpt).exists():
            print("Loading fusion model …")
            fusion_cfg = load_yaml(str(Path(cfg_path).parent / "fusion.yaml"))
            self.fusion_model = FusionModel.load_checkpoint(
                fusion_ckpt, fusion_cfg, face_cfg, pose_cfg,
                device=self.device)
        else:
            print("[INFO] No fusion checkpoint found — using face-only mode.")

        # ── MediaPipe ─────────────────────────────────────────────────────────
        self.face_detector = mp_face.FaceDetection(
            model_selection=1,
            min_detection_confidence=self.cfg["face"]["detection_confidence"],
        )
        self.pose_estimator = mp_pose.Pose(
            min_detection_confidence=self.cfg["pose"]["min_detection_confidence"],
            min_tracking_confidence=self.cfg["pose"]["min_tracking_confidence"],
            model_complexity=1,
        )
        self.hand_estimator = mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.5,
        )

        seq_len      = self.cfg["pose"]["seq_len"]
        self.pose_buf = PoseBuffer(seq_len)
        self.smoother = TemporalSmoother(
            self.cfg.get("smoothing_window", 10), self.num_classes)

        self.face_transform = make_face_transform(self.cfg["face"]["img_size"])
        print("Inference engine ready.")

    # ── Crop + classify face ──────────────────────────────────────────────────

    def _infer_face(
        self,
        frame_rgb: np.ndarray,
        detections,
    ) -> Optional[np.ndarray]:
        """Return probability vector or None if no face detected."""
        if not detections or not detections.detections:
            return None

        det   = detections.detections[0]
        bbox  = det.location_data.relative_bounding_box
        h, w  = frame_rgb.shape[:2]
        pad   = self.cfg["face"]["padding_ratio"]

        x1 = max(0, int((bbox.xmin - pad * bbox.width) * w))
        y1 = max(0, int((bbox.ymin - pad * bbox.height) * h))
        x2 = min(w, int((bbox.xmin + (1 + pad) * bbox.width) * w))
        y2 = min(h, int((bbox.ymin + (1 + pad) * bbox.height) * h))

        face_crop = frame_rgb[y1:y2, x1:x2]
        if face_crop.size == 0:
            return None

        tensor = self.face_transform(image=face_crop)["image"]
        tensor = tensor.unsqueeze(0).to(self.device)

        with torch.inference_mode(), autocast(enabled=self.use_amp):
            logits = self.face_classifier(tensor)
            probs  = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()

        return probs, (x1, y1, x2, y2)

    # ── Main frame process ────────────────────────────────────────────────────

    def process_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        face_results  = self.face_detector.process(frame_rgb)
        pose_results  = self.pose_estimator.process(frame_rgb)
        hand_results  = self.hand_estimator.process(frame_rgb)

        frame_rgb.flags.writeable = True
        out = frame_bgr.copy()

        # ── Push pose frame ───────────────────────────────────────────────────
        self.pose_buf.push(pose_results.pose_landmarks)

        # ── Draw pose skeleton ────────────────────────────────────────────────
        if (pose_results.pose_landmarks and
                self.cfg["overlay"].get("show_pose", True)):
            mp_draw.draw_landmarks(
                out,
                pose_results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_draw_styles
                    .get_default_pose_landmarks_style(),
            )

        # ── Draw hands ────────────────────────────────────────────────────────
        if hand_results.multi_hand_landmarks:
            for hand_lm in hand_results.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    out, hand_lm, mp_hands.HAND_CONNECTIONS,
                    mp_draw_styles.get_default_hand_landmarks_style(),
                    mp_draw_styles.get_default_hand_connections_style(),
                )

        # ── Face emotion ──────────────────────────────────────────────────────
        face_result = self._infer_face(frame_rgb, face_results)

        if face_result is not None:
            face_probs, (x1, y1, x2, y2) = face_result

            # ── Fusion (if available) ──────────────────────────────────────────
            if self.fusion_model is not None:
                pose_tensor = self.pose_buf.get_tensor(self.device)
                face_tensor = (self.face_transform(
                    image=cv2.cvtColor(out[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)
                )["image"].unsqueeze(0).to(self.device))
                with torch.inference_mode(), autocast(enabled=self.use_amp):
                    logits = self.fusion_model(face_tensor, pose_tensor)
                    probs  = F.softmax(logits, dim=-1).squeeze(0).cpu().numpy()
            else:
                probs = face_probs

            # Temporal smooth
            probs = self.smoother.update(probs)
            top_idx  = int(probs.argmax())
            top_prob = float(probs[top_idx])
            emotion  = self.class_names[top_idx]

            # Face bounding box
            if self.cfg["overlay"].get("show_face_bbox", True):
                color = EMOTION_COLORS.get(emotion, DEFAULT_COLOR)
                cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

            draw_top_emotion(out, emotion, top_prob,
                             x1, max(y1 - 10, 20), self.font_scale)

            # Bar chart
            if self.cfg["overlay"].get("show_bar_chart", True):
                draw_bar_chart(out, probs, self.class_names)
        else:
            self.smoother.update(
                np.ones(self.num_classes, dtype=np.float32) / self.num_classes)

        return out

    # ── Run loop ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        source = self.cfg.get("source", 0)
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.cfg.get("display_width",  1280))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cfg.get("display_height",  720))

        print("Press  Q  to quit.")
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            out_frame = self.process_frame(frame)

            # FPS counter
            cv2.putText(out_frame, "Q: quit", (out_frame.shape[1] - 90, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
            cv2.imshow("Stress & Emotion — Multimodal", out_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.face_detector.close()
        self.pose_estimator.close()
        self.hand_estimator.close()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/inference.yaml")
    args = parser.parse_args()
    MultimodalInference(args.config).run()
