from fastapi import APIRouter
from database import SessionLocal
from models.delegate import Delegate
from models.product import Product
from services.recommender import recommend_delegates as recommend_service

router = APIRouter(prefix="/recommend")

@router.get("/product/{product_id}")
def get_recommendations(product_id: int):
    db = SessionLocal()

    product = db.query(Product).get(product_id)
    delegates = db.query(Delegate).all()


    results = recommend_service(product, delegates)

    return {
        "product": product.name,
        "recommendations": results
    }