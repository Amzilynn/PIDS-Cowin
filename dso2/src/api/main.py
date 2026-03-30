from fastapi import FastAPI

from .routes import router as bo2_router


app = FastAPI(
    title="DSO2 BO2 Product Assistant API",
    version="1.0.0",
    description="RAG + LLM backend for Vital product-representing avatars.",
)

app.include_router(bo2_router)


@app.get("/")
def root() -> dict:
    return {"service": "dso2-bo2", "message": "Use /bo2 endpoints."}
