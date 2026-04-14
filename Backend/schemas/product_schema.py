from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    category: str
    description: str