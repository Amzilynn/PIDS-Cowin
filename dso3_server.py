import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 🛡️ PROTOBUF SHIELD: Force pure-python implementation to bypass 'MessageFactory' attribute errors
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

# Configuration des chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Imports des routeurs DSO3
from dso3.routes import auth_routes, delegate_routes, product_routes, recommender_routes

app = FastAPI(
    title="Avalive DSO3 API",
    description="DSO3 - Expertise and Recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes DSO3
app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
app.include_router(delegate_routes.router, prefix="/api")
app.include_router(product_routes.router, prefix="/api")
app.include_router(recommender_routes.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "DSO3 is running", "port": 8003}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
