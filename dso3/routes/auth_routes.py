import hashlib

from fastapi import APIRouter, HTTPException
from sqlalchemy import and_

from dso3.database import SessionLocal
from dso3.models.delegate import Delegate
from dso3.models.product import Product
from dso3.models.recommendation import Recommendation
from dso3.models.user import User
from dso3.schemas.auth_schema import (
    LoginRequest,
    LoginResponse,
    RecommendationPreview,
    RegisterUserRequest,
    RegisterUserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash_password(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode("utf-8")).hexdigest()


@router.post("/register", response_model=RegisterUserResponse)
def register_user(body: RegisterUserRequest) -> RegisterUserResponse:
    db = SessionLocal()
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already exists")

    user = User(
        email=body.email,
        password_hash=_hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    delegate_id = None
    if body.role == "delegate":
        base_name = (body.delegate_name or body.email.split("@")[0]).strip()
        candidate_name = base_name or "Delegate"

        suffix = 1
        unique_name = candidate_name
        while db.query(Delegate).filter(Delegate.name == unique_name).first() is not None:
            suffix += 1
            unique_name = f"{candidate_name} {suffix}"

        new_delegate = Delegate(
            user_id=user.id,
            name=unique_name,
            expertise=(body.expertise or "general").strip() or "general",
            interests=(body.interests or "general").strip() or "general",
        )
        db.add(new_delegate)
        db.commit()
        db.refresh(new_delegate)
        delegate_id = new_delegate.id

    return RegisterUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        delegate_id=delegate_id,
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    db = SessionLocal()
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.password_hash != _hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if body.role and user.role != body.role:
        raise HTTPException(status_code=403, detail="Role mismatch")

    delegate = db.query(Delegate).filter(Delegate.user_id == user.id).first()

    previews: list[RecommendationPreview] = []
    if user.role == "delegate" and delegate is not None:
        rows = (
            db.query(Recommendation, Product)
            .join(Product, Product.id == Recommendation.product_id)
            .filter(
                and_(
                    Recommendation.delegate_id == delegate.id,
                    Recommendation.id > user.last_seen_recommendation_id,
                )
            )
            .order_by(Recommendation.id.desc())
            .limit(5)
            .all()
        )

        max_rec_id = 0
        for recommendation, product in rows:
            max_rec_id = max(max_rec_id, recommendation.id)
            previews.append(
                RecommendationPreview(
                    recommendation_id=recommendation.id,
                    product_id=product.id,
                    product_name=product.name,
                    score=float(recommendation.score),
                )
            )

        if max_rec_id > user.last_seen_recommendation_id:
            user.last_seen_recommendation_id = max_rec_id
            db.commit()

    return LoginResponse(
        success=True,
        message="Login successful",
        user_id=user.id,
        role=user.role,
        delegate_id=delegate.id if delegate is not None else None,
        new_recommendations_count=len(previews),
        new_recommendations=previews,
    )
