import whisper
import sounddevice as sd
import numpy as np
import time
# Charger modèle une seule fois (important)
model = whisper.load_model("medium")  # ou "base" pour plus rapide

def record_audio(fs=16000, silence_threshold=0.02, silence_duration=1.2):
    print("🎤 Parlez...")

    recording = []
    silence_counter = 0

    chunk_duration = 0.5  # 🔥 plus petit = plus précis
    chunk_size = int(fs * chunk_duration)

    while True:
        chunk = sd.rec(chunk_size, samplerate=fs, channels=1, dtype='float32')
        sd.wait()

        volume = np.sqrt(np.mean(chunk**2))  # 🔥 RMS (meilleur que norm)

        recording.append(chunk)

        if volume < silence_threshold:
            silence_counter += chunk_duration
        else:
            silence_counter = 0

        if silence_counter >= silence_duration:
            break

    audio = np.concatenate(recording, axis=0)

    return audio.flatten().astype(np.float32), fs



def speech_to_text():
    from project.main import tts_lock  # 🔥 import local (IMPORTANT)

    # attendre que l'avatar finisse de parler
    while tts_lock.locked():
        time.sleep(0.1)

    audio, fs = record_audio()
   

    print("🧠 Transcription...")
    audio = audio / (np.max(np.abs(audio)) + 1e-6)

    result = model.transcribe(
    audio,
    fp16=False,
    language="fr",
    temperature=0.0,
    beam_size=5,
    best_of=5,
    condition_on_previous_text=False
)

    text = result.get("text", "").strip()
    lang = result.get("language", "fr")

    print("Delegué:", text)
    print("Langue détectée:", lang)

    return text, lang

def speech_to_text_file(audio_path):
    """
    Transcrit un fichier audio existant
    """
    print(f"Transcription de {audio_path} ...")
    result = model.transcribe(audio_path, fp16=False)
    text = result.get("text", "").strip()
    lang = result.get("language", "fr")
    print("Texte détecté:", text)
    print("Langue détectée:", lang)
    return text, lang