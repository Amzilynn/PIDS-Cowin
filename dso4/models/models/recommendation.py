from sqlalchemy import Column, Float, ForeignKey, Integer

from dso3.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    delegate_id = Column(Integer, ForeignKey("delegates.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
