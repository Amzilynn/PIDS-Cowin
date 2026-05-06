"""
Tone & Voice Analyzer
Captures microphone audio and extracts vocal features:
  - MFCC features
  - Pitch (F0) mean & variance
  - Speaking rate (syllables/sec approximation)
  - Energy / volume
  - Pause frequency

Runs in a background thread alongside the video pipeline.
"""

import threading
import time
import numpy as np
from dataclasses import dataclass, field
from collections import deque

try:
    import pyaudio
    import librosa
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False


@dataclass
class ToneResult:
    pitch_mean: float           # Average F0 in Hz
    pitch_variance: float       # F0 variance (monotone → low, expressive → high)
    energy: float               # RMS energy (loudness proxy)
    speaking_rate: float        # Zero-crossing rate (speech pace proxy)
    pause_ratio: float          # Fraction of time silent (0.0–1.0)
    jitter: float               # Cycle-cycle pitch variation
    shimmer: float              # Cycle-cycle energy variation
    speech_emotion_label: str   # HuBERT predicted emotion
    speech_emotion_conf: float  # HuBERT prediction confidence
    tone_label: str             # "confident" | "hesitant" | "monotone" | "energetic" | "stressed"
    overall_score: float        # 0.0–1.0 composite score


class ToneAnalyzer:
    """
    Real-time voice/tone analyzer using PyAudio + librosa.
    Runs in a background thread; call get_result() from main thread.

    Usage:
        analyzer = ToneAnalyzer()
        analyzer.start()
        ...
        result = analyzer.get_result()
        ...
        analyzer.stop()
    """

    # Audio config
    SAMPLE_RATE  = 16000
    CHUNK        = 1024          # frames per buffer
    WINDOW_SEC   = 3             # seconds of audio per analysis window
    FORMAT       = None          # set in __init__ after import

    def __init__(self):
        if not _AUDIO_AVAILABLE:
            raise ImportError(
                "Install audio dependencies:\n"
                "  pip install pyaudio librosa"
            )

        import pyaudio as _pa
        self.FORMAT = _pa.paInt16

        self._pa = _pa.PyAudio()
        self._stream = None
        self._running = False
        self._thread: threading.Thread | None = None

        # Rolling buffer of raw audio samples
        self._buffer: deque[np.ndarray] = deque(maxlen=self._buffer_size())
        self._result_lock = threading.Lock()
        self._latest_result: ToneResult = self._default_result()
        self._avatar_speaking = False

        # ── Load Audio Transformer ──────────────────────────────────
        try:
            from transformers import Wav2Vec2FeatureExtractor, HubertForSequenceClassification
            import torch
            print("[ToneAnalyzer] Loading speech emotion model (distilHuBERT)...")
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained("superb/hubert-base-superb-er")
            self._model = HubertForSequenceClassification.from_pretrained("superb/hubert-base-superb-er").to(self._device)
            self._model.eval()
            self._torch = torch
            print("[ToneAnalyzer] Speech emotion model loaded.")
        except Exception as e:
            print(f"[WARN] Failed to load distilHuBERT. Speech emotion disabled. {e}")
            self._model = None

    def set_avatar_speaking(self, speaking: bool):
        self._avatar_speaking = speaking

    def start(self):
        """Open microphone stream and start background analysis thread."""
        self._stream = self._pa.open(
            format=self.FORMAT,
            channels=1,
            rate=self.SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background thread and close microphone."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        self._pa.terminate()

    def get_result(self) -> ToneResult:
        """Thread-safe access to the latest analysis result."""
        with self._result_lock:
            return self._latest_result

    # ─── Private ───────────────────────────────────────────────────────────

    def _buffer_size(self) -> int:
        chunks_per_second = self.SAMPLE_RATE // self.CHUNK
        return chunks_per_second * self.WINDOW_SEC

    def _capture_loop(self):
        """Continuously reads audio and triggers analysis every 1.5s."""
        last_analyze_time = time.time()
        while self._running:
            try:
                raw = self._stream.read(self.CHUNK, exception_on_overflow=False)
                if self._avatar_speaking:
                    continue
                samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                self._buffer.append(samples)

                # Analyse once we have a reasonably full window AND haven't analyzed recently
                if len(self._buffer) == self._buffer.maxlen:
                    now = time.time()
                    if now - last_analyze_time >= 1.5:
                        audio = np.concatenate(list(self._buffer))
                        result = self._analyze(audio)
                        with self._result_lock:
                            self._latest_result = result
                        last_analyze_time = time.time()
            except Exception as e:
                import traceback; traceback.print_exc()
                time.sleep(0.1)

    def _analyze(self, audio: np.ndarray) -> ToneResult:
        try:
            sr = self.SAMPLE_RATE

            # ── Pitch (F0) & Jitter ──────────────────────────────
            # Using yin instead of pyin for a massive ~15x speedup
            f0 = librosa.yin(
                audio,
                fmin=65,
                fmax=2093,
                sr=sr,
            )
            f0_valid = f0[f0 > 0] if f0 is not None else np.array([])
            pitch_mean     = float(np.mean(f0_valid))     if len(f0_valid) > 0 else 0.0
            pitch_variance = float(np.var(f0_valid))      if len(f0_valid) > 0 else 0.0

            if len(f0_valid) > 1:
                jitter = float(np.mean(np.abs(np.diff(f0_valid))) / (pitch_mean + 1e-6))
            else:
                jitter = 0.0

            # ── Energy (RMS) & Shimmer ───────────────────────────
            rms    = librosa.feature.rms(y=audio)[0]
            energy = float(np.mean(rms))

            rms_valid = rms[rms > 0.01]
            if len(rms_valid) > 1:
                shimmer = float(np.mean(np.abs(np.diff(rms_valid))) / (np.mean(rms_valid) + 1e-6))
            else:
                shimmer = 0.0

            # ── Speaking rate proxy (ZCR) ─────────────────────────
            zcr          = librosa.feature.zero_crossing_rate(audio)[0]
            speaking_rate = float(np.mean(zcr))

            # ── Pause detection (silence ratio) ─────────────────
            silence_mask = rms < 0.01           # frames below threshold = silence
            pause_ratio  = float(np.mean(silence_mask))

            # ── Speech Emotion (distilHuBERT) ────────────────────
            speech_emotion_label = "neutral"
            speech_emotion_conf = 0.0

            if self._model and getattr(self, "_torch", None):
                try:
                    inputs = self._feature_extractor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
                    inputs = {k: v.to(self._device) for k, v in inputs.items()}
                    with self._torch.no_grad():
                        logits = self._model(**inputs).logits
                    probs = self._torch.nn.functional.softmax(logits, dim=-1)
                    pred_idx = self._torch.argmax(probs, dim=-1).item()
                    speech_emotion_conf = probs[0][pred_idx].item()
                    speech_emotion_label = self._model.config.id2label[pred_idx]
                except Exception:
                    pass

            # ── Tone classification ──────────────────────────────
            tone_label = self._classify_tone(
                pitch_mean, pitch_variance, energy, speaking_rate, pause_ratio,
                jitter, shimmer, speech_emotion_label
            )

            # ── Composite score ──────────────────────────────────
            overall = self._compute_score(
                pitch_variance, energy, speaking_rate, pause_ratio, jitter, shimmer
            )

            return ToneResult(
                pitch_mean=round(pitch_mean, 2),
                pitch_variance=round(pitch_variance, 2),
                energy=round(energy, 4),
                speaking_rate=round(speaking_rate, 4),
                pause_ratio=round(pause_ratio, 3),
                jitter=round(jitter, 4),
                shimmer=round(shimmer, 4),
                speech_emotion_label=speech_emotion_label,
                speech_emotion_conf=round(speech_emotion_conf, 3),
                tone_label=tone_label,
                overall_score=round(overall, 3),
            )
        except Exception as e:
            print(f"[ToneAnalyzer] Analysis error: {e}")
            return self._default_result()

    def _classify_tone(
        self,
        pitch_mean: float,
        pitch_variance: float,
        energy: float,
        speaking_rate: float,
        pause_ratio: float,
        jitter: float,
        shimmer: float,
        speech_emotion_label: str
    ) -> str:
        if pause_ratio > 0.6:
            return "hesitant"
        if energy < 0.01:
            return "hesitant"
        
        # Integrate HuBERT predictions
        if speech_emotion_label == "ang":
            return "stressed"
        if speech_emotion_label == "sad":
            return "monotone"

        # Shaky voice indicates stress/nervousness
        if jitter > 0.05 or shimmer > 0.1:
            return "stressed"

        if pitch_variance < 500 and energy < 0.03:
            return "monotone"
        if speaking_rate > 0.2 and energy > 0.05:
            return "stressed"
        if energy > 0.04 and pitch_variance > 2000:
            return "energetic"
        return "confident"

    def _compute_score(
        self,
        pitch_variance: float,
        energy: float,
        speaking_rate: float,
        pause_ratio: float,
        jitter: float,
        shimmer: float,
    ) -> float:
        """
        Higher score = better vocal performance.
        Penalizes monotone, silence, shaky voice, and overly fast pacing.
        """
        variety_score = np.clip(pitch_variance / 5000.0, 0.0, 1.0)
        energy_score  = np.clip(energy / 0.05, 0.0, 1.0)
        pace_score    = 1.0 - np.clip(abs(speaking_rate - 0.12) / 0.12, 0.0, 1.0)
        fluency_score = 1.0 - pause_ratio
        
        # Penalize high jitter (pitch tremors) and shimmer (amplitude tremors) = nervousness
        stability_score = 1.0 - np.clip((jitter / 0.1) + (shimmer / 0.2), 0.0, 1.0)

        return float(
            0.20 * variety_score +
            0.20 * energy_score +
            0.20 * pace_score +
            0.20 * fluency_score +
            0.20 * stability_score
        )

    @staticmethod
    def _default_result() -> ToneResult:
        return ToneResult(
            pitch_mean=0.0,
            pitch_variance=0.0,
            energy=0.0,
            speaking_rate=0.0,
            pause_ratio=0.0,
            jitter=0.0,
            shimmer=0.0,
            speech_emotion_label="neutral",
            speech_emotion_conf=0.0,
            tone_label="unknown",
            overall_score=0.0,
        )
