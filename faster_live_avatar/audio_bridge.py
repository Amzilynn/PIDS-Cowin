import time
import numpy as np
from collections import deque

class AudioLipSync:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        # ============================================================
        # PROFESSIONAL VISEME TABLE (industry-standard system)
        # Each letter maps to a viseme shape matching its mouth position.
        # open   = jaw drop (0=closed, 1=fully open)
        # spread = lip corners pulled wide (smile-like)
        # pucker = lips pushed forward (o/u shape)
        # ============================================================
        self.phoneme_map = {
            # --- Vowels (most visible mouth shapes) ---
            'A': {'open': 0.75, 'spread': 0.15, 'pucker': 0.00},  # "ah" - wide open
            'E': {'open': 0.45, 'spread': 0.65, 'pucker': 0.00},  # "eh/ee" - wide smile
            'I': {'open': 0.35, 'spread': 0.70, 'pucker': 0.00},  # "ih" - tight smile
            'O': {'open': 0.55, 'spread': 0.00, 'pucker': 0.50},  # "oh" - round lips
            'U': {'open': 0.25, 'spread': 0.00, 'pucker': 0.65},  # "oo" - tight pucker
            'Y': {'open': 0.40, 'spread': 0.55, 'pucker': 0.00},  # "yeh" - like E

            # --- Bilabials (lips press together) ---
            'M': {'open': 0.00, 'spread': 0.05, 'pucker': 0.10},
            'B': {'open': 0.00, 'spread': 0.05, 'pucker': 0.10},
            'P': {'open': 0.00, 'spread': 0.05, 'pucker': 0.10},

            # --- Labiodentals (lower lip to upper teeth) ---
            'F': {'open': 0.08, 'spread': 0.10, 'pucker': 0.05},
            'V': {'open': 0.08, 'spread': 0.10, 'pucker': 0.05},

            # --- Dentals / Alveolars (tip of tongue, slightly open) ---
            'T': {'open': 0.20, 'spread': 0.20, 'pucker': 0.00},
            'D': {'open': 0.20, 'spread': 0.20, 'pucker': 0.00},
            'N': {'open': 0.20, 'spread': 0.15, 'pucker': 0.00},
            'L': {'open': 0.35, 'spread': 0.15, 'pucker': 0.00},

            # --- Sibilants (teeth close, air through) ---
            'S': {'open': 0.12, 'spread': 0.40, 'pucker': 0.00},
            'Z': {'open': 0.12, 'spread': 0.40, 'pucker': 0.00},
            'C': {'open': 0.15, 'spread': 0.35, 'pucker': 0.00},  # like S

            # --- Fricatives ---
            'H': {'open': 0.30, 'spread': 0.10, 'pucker': 0.00},
            'X': {'open': 0.20, 'spread': 0.35, 'pucker': 0.00},

            # --- Velars (back of mouth) ---
            'G': {'open': 0.30, 'spread': 0.10, 'pucker': 0.00},
            'K': {'open': 0.25, 'spread': 0.10, 'pucker': 0.00},
            'Q': {'open': 0.25, 'spread': 0.10, 'pucker': 0.00},

            # --- Palatals ---
            'J': {'open': 0.25, 'spread': 0.50, 'pucker': 0.05},

            # --- Rounded consonants ---
            'W': {'open': 0.20, 'spread': 0.00, 'pucker': 0.55},  # like U
            'R': {'open': 0.35, 'spread': 0.05, 'pucker': 0.15},  # slightly rounded

            # --- Space and rest ---
            ' ':    {'open': 0.05, 'spread': 0.00, 'pucker': 0.00},
            'rest': {'open': 0.00, 'spread': 0.00, 'pucker': 0.00},
        }

        # Coarticulation buffers (3-frame weighted blend for natural transitions)
        self.smooth_open   = deque([0.0, 0.0, 0.0], maxlen=3)
        self.smooth_spread = deque([0.0, 0.0, 0.0], maxlen=3)
        self.smooth_pucker = deque([0.0, 0.0, 0.0], maxlen=3)

    def get_ratios(self, audio_features):
        if audio_features is None or len(audio_features) == 0:
            return 0.0, 0.0

        power = np.mean(np.abs(audio_features))
        target_open = 0.0
        target_spread = 0.0

        if power > 0.012:
            intensity = min(power * 8.0, 0.6)
            target_open = intensity * 0.6
            target_open += (np.random.rand() * 0.01)

        self.smooth_open.append(target_open)
        self.smooth_spread.append(target_spread)

        return np.mean(self.smooth_open), np.mean(self.smooth_spread)

    def generate_timeline_smart(self, pcm_data, text, fps):
        """Generates a per-frame viseme timeline with coarticulation blending."""
        text = text.upper()

        # Extract per-character viseme keys
        phonemes = []
        for c in text:
            if c in self.phoneme_map:
                phonemes.append(c)
            elif c.isalpha():
                phonemes.append('rest')  # unknown letter -> neutral

        if not phonemes:
            phonemes = ['rest']

        n_frames  = int(len(pcm_data) / self.sample_rate * fps)
        chunk_size = int(self.sample_rate / fps)
        timeline  = []

        # Fresh coarticulation state per utterance
        co_open   = deque([0.0, 0.0, 0.0], maxlen=3)
        co_spread = deque([0.0, 0.0, 0.0], maxlen=3)
        co_pucker = deque([0.0, 0.0, 0.0], maxlen=3)

        # Coarticulation weights: 10% two-back, 30% previous, 60% current
        WEIGHTS = [0.10, 0.30, 0.60]

        for i in range(n_frames):
            # Map frame index to a character in the text
            char_idx = int((i / max(n_frames, 1)) * len(phonemes))
            char = phonemes[min(char_idx, len(phonemes) - 1)]
            base = self.phoneme_map.get(char, self.phoneme_map['rest'])

            # Scale by audio power (intensity gate)
            start_p = i * chunk_size
            chunk = pcm_data[start_p:start_p + chunk_size]
            power = np.mean(np.abs(chunk)) if len(chunk) > 0 else 0.0
            intensity = min(power * 14.0, 1.0)

            co_open.append(base['open']   * intensity)
            co_spread.append(base['spread'] * intensity)
            co_pucker.append(base['pucker'] * intensity)

            timeline.append({
                "open":   sum(w * v for w, v in zip(WEIGHTS, co_open)),
                "spread": sum(w * v for w, v in zip(WEIGHTS, co_spread)),
                "pucker": sum(w * v for w, v in zip(WEIGHTS, co_pucker)),
            })

        return timeline


class IdleAnimator:
    def __init__(self, fps=25):
        self.start_time = time.time()
        self.fps = fps

    def get_idle_state(self):
        t = time.time() - self.start_time

        blink = 0.0
        # 3.2 second blink cycle with a guaranteed "full close" hold
        cycle_t = t % 3.2
        if cycle_t < 0.1:
            blink = cycle_t / 0.1                        # Closing glide
        elif cycle_t < 0.3:
            blink = 1.0                                   # Hold fully closed
        elif cycle_t < 0.4:
            blink = 1.0 - ((cycle_t - 0.3) / 0.1)       # Opening glide

        elif 0.6 < cycle_t < 1.0 and int(t / 3.2) % 3 == 0:
            # Occasional double blink
            dt = cycle_t - 0.6
            if   dt < 0.1: blink = dt / 0.1
            elif dt < 0.3: blink = 1.0
            else:          blink = 1.0 - ((dt - 0.3) / 0.1)

        # Natural, slightly irregular head sway (two overlapping sine waves)
        tilt = (np.sin(t * 1.0) + np.sin(t * 0.5)) * 0.012

        return {"eye_blink": blink, "head_tilt": tilt}
