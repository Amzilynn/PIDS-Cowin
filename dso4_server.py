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

# Imports des routeurs DSO4
from dso4.api.routes import router as dso4_router

app = FastAPI(
    title="Avalive DSO4 API",
    description="DSO4 - Visit Strategy Optimizer",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes DSO4
app.include_router(dso4_router)

@app.get("/")
def root():
    return {"status": "DSO4 is running", "port": 8004}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
