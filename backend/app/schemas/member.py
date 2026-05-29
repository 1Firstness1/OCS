import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.member import OrgRole


class MemberOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    department_id: uuid.UUID | None
    role: OrgRole
    position: str | None
    joined_at: datetime
    username: str | None = None
    full_name: str | None = None
    email: str | None = None

    class Config:
        from_attributes = True


class MemberUpdate(BaseModel):
    role: OrgRole | None = None
    position: str | None = None
    department_id: uuid.UUID | None = None
