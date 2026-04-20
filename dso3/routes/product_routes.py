from fastapi import APIRouter, BackgroundTasks
from dso3.database import SessionLocal
from dso3.models.delegate import Delegate
from dso3.models.product import Product
from dso3.models.recommendation import Recommendation
from dso3.models.user import User
from dso3.services.recommender import recommend_delegates
from dso3.utils.helpers import send_recommendation_email
from dso3.schemas.product_schema import ProductCreate

router = APIRouter(prefix="/products")

@router.post("/product")
def create_product(product_data: ProductCreate, background_tasks: BackgroundTasks):

    db = SessionLocal()

    # 1. CREATE PRODUCT
    new_product = Product(**product_data.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # 2. GET DELEGATES
    delegates = db.query(Delegate).all()

    # 3. COMPUTE RECOMMENDATIONS
    recommendations = recommend_delegates(new_product, delegates)

    # 4. STORE IN DB
    for rec in recommendations:
        delegate_id = rec["delegate_id"]
        db.add(Recommendation(
            product_id=new_product.id,
            delegate_id=delegate_id,
            score=rec["score"]
        ))
        
        delegate = next((d for d in delegates if d.id == delegate_id), None)
        if delegate:
            user = db.query(User).filter(User.id == delegate.user_id).first()
            if user:
                background_tasks.add_task(
                    send_recommendation_email,
                    user.email,
                    delegate.name,
                    new_product.name
                )

    db.commit()

    return {
        "message": "Product created + recommendations generated",
        "product_id": new_product.id,
        "recommendations": recommendations
    }