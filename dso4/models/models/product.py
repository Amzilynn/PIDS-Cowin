from sqlalchemy import Column, Integer, String

from dso3.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(150), nullable=False)
    description = Column(String(500), nullable=False)
