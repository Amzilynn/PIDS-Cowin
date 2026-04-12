import sys
import os
import shutil
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

from Agent.stt import speech_to_text_file
from Agent.voice import speak_text_file, get_voice
from rag.rag_build import load_or_build_rag
from rag.retriever import Retriever
from main import ask_avatar

app = FastAPI(title="Doctor Avatar API")

# CORS pour frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Charger RAG une seule fois
store = load_or_build_rag()
retriever = Retriever(store)

# Endpoint racine pour test
@app.get("/")
def root():
    return {"status": "ok"}

# POST pour chat audio
@app.post("/chat")
async def chat(audio: UploadFile = File(...)):
    audio_path = f"temp_{audio.filename}"
    with open(audio_path, "wb") as f:
        shutil.copyfileobj(audio.file, f)

    # Speech → Text
    user_input, lang = speech_to_text_file(audio_path)

    # RAG
    relevant_docs = retriever.retrieve(user_input, k=3)
    context = "\n".join(relevant_docs)

    messages = [
        {"role": "system", "content": f"Context:\n{context}"},
        {"role": "user", "content": user_input}
    ]

    # LLM
    reply = ask_avatar(messages)

    # Text → Speech
    voice = get_voice(lang)
    output_audio = f"response_{audio.filename}.mp3"
    await speak_text_file(reply, voice, output_audio)

    # Supprimer audio temporaire
    os.remove(audio_path)

    return JSONResponse({"text": reply, "audio": output_audio})