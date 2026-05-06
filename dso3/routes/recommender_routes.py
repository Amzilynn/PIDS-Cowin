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
@router.get("/notifications/{user_id}")
def get_notifications(user_id: int):
    db = SessionLocal()
    from shared.models import Notification
    try:
        notifications = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(20)
            .all()
        )
        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "is_read": n.is_read,
                "date": n.created_at.strftime("%Y-%m-%d %H:%M")
            }
            for n in notifications
        ]
    finally:
        db.close()

@router.post("/notifications/{notification_id}/read")
def mark_notification_as_read(notification_id: int):
    db = SessionLocal()
    from shared.models import Notification
    try:
        n = db.query(Notification).get(notification_id)
        if n:
            n.is_read = True
            db.commit()
            return {"status": "success"}
        return {"status": "not found"}
    finally:
        db.close()
