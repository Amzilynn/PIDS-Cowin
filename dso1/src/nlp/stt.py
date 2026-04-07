import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os

model = whisper.load_model("base")

def transcribe(audio_path):
    if not os.path.exists(audio_path):
        return ""
    result = model.transcribe(audio_path)
    return result.get("text", "").strip(), result.get("language", "unknown")

def record_and_transcribe(duration=5, fs=44100):
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    wav.write("tmp_record.wav", fs, recording)
    text, lang = transcribe("tmp_record.wav")
    return text, lang
