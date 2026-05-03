from fastapi import APIRouter
from shared.database import SessionLocal
from shared.models import Product

router = APIRouter()

@router.get("/products")
def get_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [{"id": p.id, "name": p.name, "category": p.category} for p in products]
    finally:
        db.close()
