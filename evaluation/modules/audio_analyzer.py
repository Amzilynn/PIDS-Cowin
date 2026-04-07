"""
Module Couche 3 : Audio Paralinguistique
Extrait des métriques acoustiques sur la voix avec Librosa.
"""
import librosa
import numpy as np
import warnings
warnings.filterwarnings("ignore")

class AudioAnalyzer:
    def __init__(self, sample_rate=16000):
        self.sr = sample_rate

    def process_chunk(self, audio_chunk):
        """
        Calcule les features acoustiques de bas niveau sur un fragment audio (numpy array).
        Retourne l'énergie (volume), pitch (F0), et détecte si la personne parle.
        """
        results = {
            "energy": 0.0,
            "pitch_mean": 0.0,
            "is_speaking": False
        }
        
        if audio_chunk is None or len(audio_chunk) == 0:
            return results

        # 1. Énergie (RMS - Root Mean Square) pour le volume
        rms = librosa.feature.rms(y=audio_chunk)[0]
        energy = float(np.mean(rms))
        results["energy"] = energy

        # Seuil basique pour considérer qu'il y a de la parole (à affiner selon le micro)
        if energy > 0.002:
            results["is_speaking"] = True
            
            # 2. Pitch (Fréquence fondamentale F0) - Donne l'intonation de la voix
            # Le PyIN est très robuste pour la voix humaine
            f0, voiced_flag, voiced_probs = librosa.pyin(
                audio_chunk, 
                fmin=librosa.note_to_hz('C2'), 
                fmax=librosa.note_to_hz('C7'),
                sr=self.sr
            )
            # Exclure les silences/bruits (NaN)
            f0_valid = f0[~np.isnan(f0)]
            if len(f0_valid) > 0:
                results["pitch_mean"] = float(np.mean(f0_valid))

        return results

def run_test():
    """
    Test microphonique court en direct.
    (Nécessite la librairie 'sounddevice' pour l'enregistrement test)
    """
    print("--------------------------------------------------")
    print("Démarrage du test AudioAnalyzer (Librosa)...")
    try:
        import sounddevice as sd
    except ImportError:
        print("❌ Installez sounddevice ('pip install sounddevice') pour tester votre micro en direct.")
        return

    analyzer = AudioAnalyzer(sample_rate=16000)
    duration = 4 # secondes d'enregistrement test
    print(f"🎙️ Parlez maintenant ! (Enregistrement de {duration}s...)")
    
    # Capture audio via le micro par défaut
    audio = sd.rec(int(duration * 16000), samplerate=16000, channels=1, dtype='float32')
    sd.wait()
    print("✅ Enregistrement terminé. Analyse en cours...\n")
    
    # Aplatir en tableau 1D pour Librosa
    audio_flat = audio.flatten()
    
    res = analyzer.process_chunk(audio_flat)
    print("----- RÉSULTATS ACOUSTIQUES -----")
    print(f"Voix détectée   : {'OUI' if res['is_speaking'] else 'NON'}")
    print(f"Volume (Energy) : {res['energy']:.4f}")
    if res['is_speaking']:
         print(f"Pitch (Voix F0) : {res['pitch_mean']:.1f} Hz")
         if res['pitch_mean'] > 180:
             print("-> Timbre perçu comme plutôt aigu :)")
         else:
             print("-> Timbre perçu comme plutôt grave :)")
    print("---------------------------------")

if __name__ == "__main__":
    run_test()
