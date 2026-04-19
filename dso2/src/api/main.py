import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
PROJECT_ROOT = os.path.join(BASE_DIR, "..", "..", "..")
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from api.routes.chat import router as chat_router, set_manager
from api.session_manager import SessionManager

# DSO4 — Visit Strategy Optimizer routes
try:
    from dso4.api.routes import router as dso4_router
    DSO4_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] DSO4 module not loaded: {e}")
    DSO4_AVAILABLE = False

manager = SessionManager()
set_manager(manager)

app = FastAPI(
    title="VITAL AI Delegate API",
    description="French medical/commercial delegate agent — DSO2 + DSO4",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DSO2 — Chat routes
app.include_router(chat_router)

# DSO4 — Visit Strategy routes
if DSO4_AVAILABLE:
    app.include_router(dso4_router)
    print("[OK] DSO4 Visit Strategy routes mounted")


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "modules": {
            "dso2_chat": True,
            "dso4_tournee": DSO4_AVAILABLE,
        },
        "active_sessions": manager.count_sessions(),
        "timestamp": datetime.utcnow()
    }
