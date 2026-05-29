import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.invitation import InvitationStatus


class InvitationCreate(BaseModel):
    email: EmailStr


class InvitationOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    inviter_id: uuid.UUID
    email: str
    status: InvitationStatus
    token: str
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True

