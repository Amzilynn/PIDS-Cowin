import whisper
import sounddevice as sd
import numpy as np

# Charger modèle une seule fois (important)
model = whisper.load_model("small")  # ou "base" pour plus rapide

def record_audio(fs=16000, silence_threshold=0.01, silence_duration=1.5):
    print("🎤 Parlez...")

    recording = []
    silence_counter = 0
    chunk_duration = 2  # 300 ms
    chunk_size = int(fs * chunk_duration)

    while True:
        chunk = sd.rec(chunk_size, samplerate=fs, channels=1)
        sd.wait()

        volume = np.linalg.norm(chunk)

        recording.append(chunk)

        if volume < silence_threshold:
            silence_counter += chunk_duration
        else:
            silence_counter = 0

        # stop si silence prolongé
        if silence_counter >= silence_duration:
            break

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

