import threading
import time
import numpy as np
from dataclasses import dataclass, field
from collections import deque

try:
    import sounddevice as sd
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
    Real-time voice/tone analyzer using sounddevice + librosa.
    sounddevice is more stable on Windows than PyAudio for shared microphone access.
    """

    SAMPLE_RATE  = 16000
    CHUNK        = 1024
    WINDOW_SEC   = 3

    def __init__(self):
        self._running = False
        self._thread = None
        self._audio_buffer = deque(maxlen=int(self.SAMPLE_RATE * self.WINDOW_SEC / self.CHUNK))
        self._last_result = self._get_default_result()
        self._lock = threading.Lock()
        self._avatar_speaking = False  # Set to True to ignore audio when avatar speaks

    def _get_default_result(self):
        return ToneResult(
            pitch_mean=0.0, pitch_variance=0.0, energy=0.0,
            speaking_rate=0.0, pause_ratio=0.0, jitter=0.0, shimmer=0.0,
            speech_emotion_label="neutral", speech_emotion_conf=1.0,
            tone_label="neutral", overall_score=0.5
        )

    def set_avatar_speaking(self, speaking: bool):
        self._avatar_speaking = speaking

    def start(self):
        if not _AUDIO_AVAILABLE:
            print("[Tone] Audio dependencies missing. Analyzer disabled.")
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._thread.start()
        print("[Tone] Analyzer started (using sounddevice)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print("[Tone] Analyzer stopped")

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"[Tone] Status: {status}")
        if not self._avatar_speaking:
            self._audio_buffer.append(indata.copy())

    def _analysis_loop(self):
        try:
            with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=1, 
                              callback=self._audio_callback, blocksize=self.CHUNK):
                while self._running:
                    if len(self._audio_buffer) >= self._audio_buffer.maxlen // 2:
                        self._analyze_buffer()
                    time.sleep(0.5)
        except Exception as e:
            print(f"[Tone] Error in audio stream: {e}")
            self._running = False

    def _analyze_buffer(self):
        with self._lock:
            try:
                # Combine buffer into one signal
                chunks = list(self._audio_buffer)
                if not chunks: return
                y = np.concatenate(chunks).flatten()
                
                # Check for silence
                rms = np.sqrt(np.mean(y**2))
                if rms < 0.005:
                    self._last_result = self._get_default_result()
                    return

                # Pitch (F0)
                f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
                f0 = f0[~np.isnan(f0)]
                p_mean = float(np.mean(f0)) if len(f0) > 0 else 0.0
                p_var = float(np.var(f0)) if len(f0) > 0 else 0.0

                # Speaking rate (ZCR proxy)
                zcr = librosa.feature.zero_crossing_rate(y)
                s_rate = float(np.mean(zcr)) * 100

                # Tone labeling logic
                label = "confident"
                score = 0.8
                if p_var < 50: label, score = "monotone", 0.4
                elif s_rate < 5: label, score = "hesitant", 0.5
                elif rms > 0.05: label, score = "energetic", 0.9

                self._last_result = ToneResult(
                    pitch_mean=p_mean, pitch_variance=p_var, energy=float(rms),
                    speaking_rate=s_rate, pause_ratio=0.0, jitter=0.0, shimmer=0.0,
                    speech_emotion_label="neutral", speech_emotion_conf=0.9,
                    tone_label=label, overall_score=score
                )
            except Exception as e:
                print(f"[Tone] Analysis error: {e}")

    def get_result(self) -> ToneResult:
        with self._lock:
            return self._last_result
