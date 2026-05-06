from sqlalchemy import Column, ForeignKey, Integer, String

from dso3.database import Base


class Delegate(Base):
    __tablename__ = "delegates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    expertise = Column(String(255), nullable=False)
    interests = Column(String(255), nullable=False)
    specification = Column(String(255), nullable=True)
