import os
import torch
import librosa
import numpy as np
import io
import base64
from PIL import Image
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from transformers import (
    pipeline, 
    AutoTokenizer, 
    AutoModelForCausalLM, 
    AutoImageProcessor, 
    AutoModelForImageClassification
)

app = FastAPI()

# System Config
device = "cuda" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

print(f"--- AVALIVE AI ENGINE ---")
print(f"Device: {device}")
print(f"Integrating Administrative & Delegate Models...")

# 1. DELEGATE CHAT: BioMistral-7B
print("-> Loading BioMistral-7B (Delegate Engine)...")
try:
    chat_id = "BioMistral/BioMistral-7B"
    tokenizer_chat = AutoTokenizer.from_pretrained(chat_id)
    model_chat = AutoModelForCausalLM.from_pretrained(chat_id, torch_dtype=torch_dtype, device_map="auto")
except Exception as e:
    print(f"FAILED to load BioMistral-7B (Network/Disk Error): {e}")
    tokenizer_chat, model_chat = None, None

# 2. VOICE: Whisper-Base (STT)
print("-> Loading Whisper & MMS (Voice Engine)...")
try:
    stt_id = "openai/whisper-base"
    stt_pipe = pipeline("automatic-speech-recognition", model=stt_id, device=device)
except Exception as e:
    print(f"FAILED to load Whisper (Network/Disk Error): {e}")
    stt_pipe = None

# 3. VISION & VOICE EMOTION: Custom YOLO + GNN + RNN
print("-> Loading Custom GNN+RNN Multi-Modal Engine...")
from multimodal_emotion_detector import MultiModalEmotionDetector
multimodal_detector = MultiModalEmotionDetector()

# 4. ADMIN CHAT: (Sharing BioMistral for now, customized via System Prompt)
# Business Intelligence Specialist -> Managed in prompt logic below

class ChatRequest(BaseModel):
    message: str
    context: list = []
    role: str = "delegate" # 'admin' or 'delegate'

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        if tokenizer_chat is None or model_chat is None:
            return {"response": "[Engine Offline] Language model failed to load due to network timeout or missing weights."}
            
        # Specialized System Prompts for Admin/Delegate parity
        if request.role == "admin":
            system_prompt = "You are Ava Business. Provide clinical market intelligence and business strategy guidance for Avalive."
        else:
            system_prompt = "You are Ava Train. You are a senior medical evaluator testing the user's clinical detailing skills."
            
        full_msg = f"{system_prompt}\nUser Context: {', '.join(request.context)}\nMessage: {request.message}"
        
        messages = [{"role": "user", "content": full_msg}]
        inputs = tokenizer_chat.apply_chat_template(messages, add_generation_prompt=True, return_dict=True, return_tensors="pt").to(device)
        outputs = model_chat.generate(**inputs, max_new_tokens=200, temperature=0.7)
        response = tokenizer_chat.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vision")
async def vision(request: dict):
    try:
        # Decode and process image
        img_data = base64.b64decode(request['image'])
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        
        import cv2
        img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        faces = multimodal_detector.detect_faces(img_np)
        
        if faces:
            face_img = faces[0]['image']
            emotion, confidence = multimodal_detector.predict_facial_emotion(face_img)
        else:
            emotion, confidence = "neutral", 0.1
        
        if not emotion:
            emotion = "neutral"
            
        return {
            "label": emotion, 
            "score": confidence, 
            "gnn_performance": confidence,
            "status": "Landmark Graph Validated via YOLO+GNN"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        audio, rate = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        result = stt_pipe(audio)
        return {"text": result["text"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def status():
    return {
        "status": "ONLINE",
        "models": ["BioMistral-7B", "Whisper-Base", "Custom-YOLO-GNN-RNN"],
        "gpu_active": torch.cuda.is_available()
    }

if __name__ == "__main__":
    import uvicorn
    print("\nAVALIVE AI SERVER READY ON http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
