import whisper
import sounddevice as sd
import numpy as np
import threading

# Charger modèle une seule fois (important)
model = whisper.load_model("small")  # ou "base" pour plus rapide

# Events pour contrôler le Push-to-Talk depuis l'API
recording_start_event = threading.Event()
recording_stop_event = threading.Event()
is_recording_active = False

def record_audio(fs=16000, silence_threshold=0.01, silence_duration=1.5):
    global is_recording_active
    
    # On vide les events par sécurité
    recording_start_event.clear()
    recording_stop_event.clear()
    
    print("⏳ En attente du bouton Push-to-Talk pour parler...")
    
    # 1. Attendre le signal de démarrage
    recording_start_event.wait()
    recording_start_event.clear()
    
    print("🔴 Enregistrement en cours...")
    is_recording_active = True
    
    recording = []
    chunk_duration = 0.5  # 500 ms (plus fluide)
    chunk_size = int(fs * chunk_duration)
    
    # 2. Enregistrer tant qu'on n'a pas reçu le signal de fin
    while not recording_stop_event.is_set():
        chunk = sd.rec(chunk_size, samplerate=fs, channels=1)
        sd.wait()
        recording.append(chunk)

    recording_stop_event.clear()
    is_recording_active = False
    
    print("⏹️ Enregistrement terminé.")

    if len(recording) == 0:
        # Fallback pour éviter les erreurs
        return np.zeros(fs, dtype=np.float32), fs

    audio = np.concatenate(recording, axis=0)

    # Retourner le tableau audio directement (pas de fichier)
    return audio.flatten().astype(np.float32), fs

def speech_to_text():
    audio, fs = record_audio()

    print("🧠 Transcription...")

    # Transcrire directement le tableau audio (pas de fichier, pas besoin de ffmpeg)
    result = model.transcribe(audio, fp16=False, language="fr")

    text = result.get("text", "").strip()
    lang = result.get("language", "fr")

    print("Delegué:", text)
    print("Langue détectée:", lang)

    return text, lang