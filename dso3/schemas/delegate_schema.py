from pydantic import BaseModel


class DelegateCreate(BaseModel):
    name: str
    expertise: str
    interests: str
    specification: str | None = None
    user_email: str | None = None
    user_password: str | None = None
