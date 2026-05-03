from fastapi import APIRouter
from shared.database import SessionLocal
from shared.models import Delegate

router = APIRouter()

@router.get("/delegates")
def get_delegates():
    db = SessionLocal()
    try:
        delegates = db.query(Delegate).all()
        return [{"id": d.id, "name": f"{d.first_name} {d.last_name}", "expertise": d.expertise} for d in delegates]
    finally:
        db.close()
