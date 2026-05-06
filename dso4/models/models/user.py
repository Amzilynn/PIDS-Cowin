from sqlalchemy import Boolean, Column, Integer, String

from dso3.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(200), nullable=False, unique=True, index=True)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(50), nullable=False, default="delegate")
    last_seen_recommendation_id = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
