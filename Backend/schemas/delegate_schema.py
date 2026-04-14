from pydantic import BaseModel

class DelegateCreate(BaseModel):
    name: str
    expertise: str
    interests: str