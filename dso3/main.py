from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dso3.routes import delegate_routes, product_routes, recommender_routes

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(delegate_routes.router)
app.include_router(product_routes.router)
app.include_router(recommender_routes.router)

@app.get("/")
def home():
    return {"message": "DSO3 API with Embedding running 🚀"}