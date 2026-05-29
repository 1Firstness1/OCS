import uuid
from datetime import datetime
from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class DepartmentOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    member_count: int = 0

    class Config:
        from_attributes = True
