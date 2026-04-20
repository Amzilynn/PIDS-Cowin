from fastapi import APIRouter, HTTPException
import hashlib

from dso3.database import SessionLocal
from dso3.models.delegate import Delegate
from dso3.models.product import Product
from dso3.models.recommendation import Recommendation
from dso3.models.user import User
from dso3.schemas.delegate_schema import DelegateCreate

router = APIRouter(prefix="/delegates")


def _hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()

@router.post("/")
def create_delegate(data: DelegateCreate):
    db = SessionLocal()

    if not data.user_email or not data.user_password:
        raise HTTPException(status_code=400, detail="user_email and user_password are required to create a delegate")

    existing_user = db.query(User).filter(User.email == data.user_email).first()
    if existing_user is not None:
        raise HTTPException(status_code=409, detail="User email already exists")

    delegate_payload = {
        "name": data.name,
        "expertise": data.expertise,
        "interests": data.interests,
        "specification": data.specification,
    }
    user = User(
        email=data.user_email,
        password_hash=_hash_password(data.user_password),
        role="delegate",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    delegate = Delegate(user_id=user.id, **delegate_payload)

    db.add(delegate)
    db.commit()
    db.refresh(delegate)

    return delegate

@router.get("/")
def get_delegates():
    db = SessionLocal()
    return db.query(Delegate).all()


@router.get("/{delegate_id}/recommended-products")
def get_recommended_products(delegate_id: int, limit: int = 20):
    db = SessionLocal()
    delegate = db.query(Delegate).filter(Delegate.id == delegate_id).first()
    user = db.query(User).filter(User.id == delegate.user_id).first() if delegate else None
    if user is None:
        return {"delegate_id": delegate_id, "new_count": 0, "items": []}

    rows = (
        db.query(Recommendation, Product)
        .join(Product, Product.id == Recommendation.product_id)
        .filter(Recommendation.delegate_id == delegate_id)
        .order_by(Recommendation.id.desc())
        .limit(max(limit, 1))
        .all()
    )

    return {
        "delegate_id": delegate_id,
        "new_count": len(rows),
        "items": [
            {
                "recommendation_id": recommendation.id,
                "product_id": product.id,
                "product_name": product.name,
                "category": product.category,
                "description": product.description,
                "score": float(recommendation.score),
            }
            for recommendation, product in rows
        ],
    }


@router.post("/{delegate_id}/recommended-products/mark-seen")
def mark_recommendations_seen(delegate_id: int):
    db = SessionLocal()
    delegate = db.query(Delegate).filter(Delegate.id == delegate_id).first()
    user = db.query(User).filter(User.id == delegate.user_id).first() if delegate else None
    if user is None:
        return {"message": "No linked user found", "delegate_id": delegate_id, "last_seen": 0}

    latest = (
        db.query(Recommendation)
        .filter(Recommendation.delegate_id == delegate_id)
        .order_by(Recommendation.id.desc())
        .first()
    )
    user.last_seen_recommendation_id = latest.id if latest else 0
    db.commit()

    return {
        "message": "Recommendations marked as seen",
        "delegate_id": delegate_id,
        "last_seen": user.last_seen_recommendation_id,
    }