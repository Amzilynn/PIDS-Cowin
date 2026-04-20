from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


RoleType = Literal["admin", "delegate", "medecin"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    role: RoleType = Field(default="delegate")


class RecommendationPreview(BaseModel):
    recommendation_id: int
    product_id: int
    product_name: str
    score: float


class LoginResponse(BaseModel):
    success: bool
    message: str
    user_id: int
    role: RoleType
    delegate_id: int | None = None
    new_recommendations_count: int = 0
    new_recommendations: list[RecommendationPreview] = []


class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    role: RoleType = Field(default="delegate")
    delegate_name: str | None = None
    expertise: str | None = None
    interests: str | None = None
    specification: str | None = None

    @model_validator(mode="after")
    def validate_role_delegate_link(self) -> "RegisterUserRequest":
        if self.role != "delegate" and any([self.delegate_name, self.expertise, self.interests, self.specification]):
            raise ValueError("delegate details are only allowed for delegate role")
        return self


class RegisterUserResponse(BaseModel):
    id: int
    email: str
    role: RoleType
    delegate_id: int | None = None
