from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.RECRUITER
    organization_name: Optional[str] = None
    client_code: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str
    role: str
    organization_id: Optional[int] = None
    organization_name: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: int
    name: str
    org_type: str
    client_code: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    organization_id: Optional[int]
    organization: Optional[OrganizationResponse] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

