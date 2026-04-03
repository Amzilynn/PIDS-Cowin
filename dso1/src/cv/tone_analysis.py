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
        sr = self.SAMPLE_RATE

        # ── Pitch (F0) ───────────────────────────────────────
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

        # ── Energy (RMS) ─────────────────────────────────────
        rms    = librosa.feature.rms(y=audio)[0]
        energy = float(np.mean(rms))

        # ── Speaking rate proxy (ZCR) ─────────────────────────
        zcr          = librosa.feature.zero_crossing_rate(audio)[0]
        speaking_rate = float(np.mean(zcr))

        # ── Pause detection (silence ratio) ─────────────────
        silence_mask = rms < 0.01           # frames below threshold = silence
        pause_ratio  = float(np.mean(silence_mask))

        # ── Tone classification ──────────────────────────────
        tone_label = self._classify_tone(
            pitch_mean, pitch_variance, energy, speaking_rate, pause_ratio
        )

        # ── Composite score ──────────────────────────────────
        overall = self._compute_score(
            pitch_variance, energy, speaking_rate, pause_ratio
        )

        return ToneResult(
            pitch_mean=round(pitch_mean, 2),
            pitch_variance=round(pitch_variance, 2),
            energy=round(energy, 4),
            speaking_rate=round(speaking_rate, 4),
            pause_ratio=round(pause_ratio, 3),
            tone_label=tone_label,
            overall_score=round(overall, 3),
        )

    def _classify_tone(
        self,
        pitch_mean: float,
        pitch_variance: float,
        energy: float,
        speaking_rate: float,
        pause_ratio: float,
    ) -> str:
        if pause_ratio > 0.6:
            return "hesitant"
        if energy < 0.01:
            return "hesitant"
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
    ) -> float:
        """
        Higher score = better vocal performance.
        Penalizes monotone, silence, and overly fast pacing.
        """
        variety_score = np.clip(pitch_variance / 5000.0, 0.0, 1.0)
        energy_score  = np.clip(energy / 0.05, 0.0, 1.0)
        pace_score    = 1.0 - np.clip(abs(speaking_rate - 0.12) / 0.12, 0.0, 1.0)
        fluency_score = 1.0 - pause_ratio

        return float(
            0.25 * variety_score +
            0.25 * energy_score +
            0.25 * pace_score +
            0.25 * fluency_score
        )

    @staticmethod
    def _default_result() -> ToneResult:
        return ToneResult(
            pitch_mean=0.0,
            pitch_variance=0.0,
            energy=0.0,
            speaking_rate=0.0,
            pause_ratio=0.0,
            tone_label="unknown",
            overall_score=0.0,
        )
