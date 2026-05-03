from fastapi import APIRouter
from shared.database import SessionLocal
from shared.models import Delegate
from shared.models import Product
from dso3.services.recommender import recommend_delegates as recommend_service

router = APIRouter()

@router.get("/product/{product_id}")
def get_recommendations(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).get(product_id)
        if not product:
            return {"error": "Product not found"}
        results = recommend_service(db, product)

        return {
            "product": product.name,
            "recommendations": results
        }
    finally:
        db.close()

@router.get("/delegate/{delegate_id}")
def get_delegate_recommendations(delegate_id: int):
    db = SessionLocal()
    from shared.models import Recommendation, Product
    try:
        results = (
            db.query(Recommendation, Product)
            .join(Product, Recommendation.product_id == Product.id)
            .filter(Recommendation.delegate_id == delegate_id)
            .order_by(Recommendation.id.desc())
            .all()
        )
        return [
            {
                "recommendation_id": rec.id,
                "product_id": prod.id,
                "product_name": prod.name,
                "score": float(rec.score),
                "gamme_id": prod.gamme_id,
                "gamme_name": prod.gamme.name if prod.gamme else "Sans Gamme",
                "category": prod.category,
                "description": prod.description
            }
            for rec, prod in results
        ]
    finally:
        db.close()
