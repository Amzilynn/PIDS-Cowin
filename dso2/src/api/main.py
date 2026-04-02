import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
sys.path.insert(0, SRC_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from api.routes.chat import router as chat_router, set_manager
from api.session_manager import SessionManager

manager = SessionManager()
set_manager(manager)

app = FastAPI(
    title="VITAL AI Delegate API",
    description="French medical/commercial delegate agent with Ollama",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "active_sessions": manager.count_sessions(),
        "timestamp": datetime.utcnow()
    }
