from fastapi import APIRouter
from dso3.database import SessionLocal
from dso3.models.delegate import Delegate
from dso3.schemas.delegate_schema import DelegateCreate

router = APIRouter(prefix="/delegates")

@router.post("/")
def create_delegate(data: DelegateCreate):
    db = SessionLocal()

    delegate = Delegate(**data.dict())

    db.add(delegate)
    db.commit()
    db.refresh(delegate)

    return delegate

@router.get("/")
def get_delegates():
    db = SessionLocal()
    return db.query(Delegate).all()