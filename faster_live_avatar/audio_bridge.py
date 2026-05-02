import time
import numpy as np
from collections import deque

class AudioLipSync:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        # 1. Phoneme Mapping with 'Over-Compensation' Multipliers
        # We aim for higher values to overcome the AI's natural dampening.
        self.phoneme_map = {
            'A': {'open': 0.8, 'spread': 0.1, 'pucker': 0.0},
            'E': {'open': 0.5, 'spread': 0.6, 'pucker': 0.0},
            'I': {'open': 0.4, 'spread': 0.5, 'pucker': 0.0},
            'O': {'open': 0.6, 'spread': -0.2, 'pucker': 0.4}, # Toned down significantly
            'U': {'open': 0.3, 'spread': -0.3, 'pucker': 0.5}, # Toned down significantly
            'M': {'open': 0.01, 'spread': 0.0, 'pucker': 0.0},
            'B': {'open': 0.01, 'spread': 0.0, 'pucker': 0.0},
            'P': {'open': 0.01, 'spread': 0.0, 'pucker': 0.0},
            'F': {'open': 0.1, 'spread': 0.2, 'pucker': 0.1},
            'V': {'open': 0.1, 'spread': 0.2, 'pucker': 0.1},
            'L': {'open': 0.4, 'spread': 0.1, 'pucker': 0.0},
            'rest': {'open': 0.0, 'spread': 0.0, 'pucker': 0.0}
        }
        
        # 2. High-Speed Smoothing (Tuned for 25 FPS)
        self.smooth_open = deque(maxlen=3) # Faster response
        self.smooth_spread = deque(maxlen=3)
        
    def get_ratios(self, audio_features):
        if audio_features is None or len(audio_features) == 0:
            return 0.0, 0.0
            
        # Simplified power-based phoneme detection
        power = np.mean(np.abs(audio_features))
        
        target_open = 0.0
        target_spread = 0.0
        
        if power > 0.012: # Slightly higher threshold
            intensity = min(power * 8.0, 0.6) # Very conservative gain
            target_open = intensity * 0.6      
            target_spread = 0.0 
            target_open += (np.random.rand() * 0.01)
        
        self.smooth_open.append(target_open)
        self.smooth_spread.append(target_spread)
        
        return np.mean(self.smooth_open), np.mean(self.smooth_spread)

    def generate_timeline_smart(self, pcm_data, text, fps):
        """Generates a list of lip ratios using text-based phoneme alignment."""
        text = text.upper()
        # Filter only letters we have in map
        phonemes = [c for c in text if c in self.phoneme_map or c == ' ']
        if not phonemes: phonemes = ['rest']
        
        n_frames = int(len(pcm_data) / self.sample_rate * fps)
        chunk_size = int(self.sample_rate / fps)
        timeline = []
        
        for i in range(n_frames):
            # Map current time to a character in the text
            char_idx = int((i / n_frames) * len(phonemes))
            char = phonemes[min(char_idx, len(phonemes)-1)]
            
            # Get base shape for this character
            base_shape = self.phoneme_map.get(char, self.phoneme_map['rest']).copy()
            
            # Use audio power to scale the intensity
            start_p = i * chunk_size
            chunk = pcm_data[start_p:start_p + chunk_size]
            power = np.mean(np.abs(chunk)) if len(chunk) > 0 else 0
            intensity = min(power * 14.0, 0.8) # Increased gain and removed buffer
            
            # Combine text shape with audio intensity
            timeline.append({
                "open": base_shape['open'] * intensity,
                "spread": base_shape['spread'] * intensity,
                "pucker": base_shape['pucker'] * intensity
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
            blink = cycle_t / 0.1  # Closing glide
        elif cycle_t < 0.3:
            blink = 1.0            # Hold fully closed for 0.2s (Guarantees at least 1 frame at 6 FPS)
        elif cycle_t < 0.4:
            blink = 1.0 - ((cycle_t - 0.3) / 0.1)  # Opening glide
            
        elif 0.6 < cycle_t < 1.0 and int(t / 3.2) % 3 == 0:
            # Occasional double blink (faster)
            dt = cycle_t - 0.6
            if dt < 0.1: blink = dt / 0.1
            elif dt < 0.3: blink = 1.0
            else: blink = 1.0 - ((dt - 0.3) / 0.1)
            
        # Natural, slightly irregular head sway (faster movement)
        # Primary sway: ~6 second period (1.0), Secondary drift: ~12 second period (0.5)
        tilt = (np.sin(t * 1.0) + np.sin(t * 0.5)) * 0.012
        
        return {"eye_blink": blink, "head_tilt": tilt}
