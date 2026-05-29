import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.organization import OrganizationCategory


class OrganizationCreate(BaseModel):
    name: str
    description: str | None = None
    category: OrganizationCategory = OrganizationCategory.OTHER
    data: dict | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: OrganizationCategory | None = None
    data: dict | None = None


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: OrganizationCategory
    data: dict | None
    owner_id: uuid.UUID
    is_active: bool
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True