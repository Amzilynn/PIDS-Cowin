from fastapi import FastAPI
from routes import delegate_routes, product_routes, recommender_routes

app = FastAPI()

app.include_router(delegate_routes.router)
app.include_router(product_routes.router)
app.include_router(recommender_routes.router)

@app.get("/")
def home():
    return {"message": "DSO3 API with Embedding running 🚀"}