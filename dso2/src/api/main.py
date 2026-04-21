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

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ... (existing imports)

# DSO2 — Chat routes
app.include_router(chat_router)

# Serve the Frontend HTML
@app.get("/")
async def read_index():
    index_path = os.path.join(PROJECT_ROOT, "dso2", "frontend", "main.html")
    return FileResponse(index_path)

# Mount static files for Avatar Videos
ASSETS_DIR = os.path.join(PROJECT_ROOT, "dso2", "frontend", "assets")
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
    print(f"[OK] Assets mounted at /assets from {ASSETS_DIR}")
else:
    print(f"[WARNING] Assets directory not found at {ASSETS_DIR}")

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
