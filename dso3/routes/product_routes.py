from fastapi import APIRouter
from dso3.database import SessionLocal
from dso3.models.delegate import Delegate
from dso3.models.product import Product
from dso3.models.recommendation import Recommendation
from dso3.services.recommender import recommend_delegates
from dso3.schemas.product_schema import ProductCreate

router = APIRouter(prefix="/products")

@router.post("/product")
def create_product(product_data: ProductCreate):

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
        db.add(Recommendation(
            product_id=new_product.id,
            delegate_id=rec["delegate_id"],
            score=rec["score"]
        ))

    db.commit()

    return {
        "message": "Product created + recommendations generated",
        "product_id": new_product.id,
        "recommendations": recommendations
    }