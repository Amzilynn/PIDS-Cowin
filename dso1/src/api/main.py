import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
sys.path.insert(0, SRC_DIR)

from api.routes.training import router as training_router
from api.routes.auth import router as auth_router
from api.routes.admin import router as admin_router

app = FastAPI(
    title="VITAL AI - DSO1 Training API",
    description="API for Medical Delegate Training session with continuous CV and Tone evaluation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(training_router, prefix="/api/training", tags=["Training"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])

# Montage des dossiers statiques
# On s'assure que le chemin est absolu vers dso1/reports
reports_dir = os.path.abspath(os.path.join(SRC_DIR, "..", "reports"))
os.makedirs(reports_dir, exist_ok=True)
print(f"[Main] Serving reports from: {reports_dir}")
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")

@app.get("/health")
def health_check():
    from api.session_manager import manager
    return {
        "status": "ok",
        "session_active": manager.is_active
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
