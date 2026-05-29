import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.user import PlatformRole


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    full_name: str
    platform_role: PlatformRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None


class UserAdminUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    platform_role: PlatformRole | None = None
    is_active: bool | None = None


class ReauthRequest(BaseModel):
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
