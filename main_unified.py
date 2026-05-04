import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 1. Configuration des chemins — ordre CRITIQUE pour éviter les conflits
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DSO1_SRC = os.path.join(BASE_DIR, "dso1", "src")
DSO1_API = os.path.join(DSO1_SRC, "api")

# a) Racine du projet en premier (pour dso3.*, dso4.*, shared.*)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
# b) DSO1/src en second (pour les imports relatifs DSO1)
if DSO1_SRC not in sys.path:
    sys.path.insert(1, DSO1_SRC)
# c) DSO1/src/api en troisième (pour api.routes.*)
if DSO1_API not in sys.path:
    sys.path.insert(2, DSO1_API)

# 2. Imports des routeurs DSO1
from api.routes.training import router as training_router
from api.routes.auth import router as dso1_auth_router
from api.routes.admin import router as dso1_admin_router

# 3. Imports des routeurs DSO3
from dso3.routes import auth_routes, delegate_routes, product_routes, recommender_routes

# 3b. Import du routeur DSO4
from dso4.api.routes import router as dso4_router

# 4. Création de l'application unifiée
app = FastAPI(
    title="Avalive Unified API",
    description="Fusion de DSO1 (Entraînement) et DSO3 (Recommandations)",
    version="2.0.0"
)

# 5. Configuration CORS (pour le front React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 6. Montage des dossiers statiques (Rapports DSO1)
reports_dir = os.path.join(BASE_DIR, "dso1", "reports")
os.makedirs(reports_dir, exist_ok=True)
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")

# 7. Inclusion des routes DSO3 (Priorité au nouvel Auth unifié)
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
app.include_router(delegate_routes.router, prefix="/api")
app.include_router(product_routes.router, prefix="/api")
app.include_router(recommender_routes.router, prefix="/api")

# 7b. Inclusion des routes DSO4 (Optimisation Tournées)
app.include_router(dso4_router)

# 8. Inclusion des routes DSO1 (Training et Admin)
app.include_router(training_router, prefix="/api/training", tags=["DSO1-Training"])
app.include_router(dso1_admin_router, prefix="/api/admin", tags=["DSO1-Admin"])

@app.get("/")
def root():
    return {"status": "Avalive Unified API is running", "ports": {"unified": 8001}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_unified:app", host="0.0.0.0", port=8001, reload=True)
