import uuid
from datetime import datetime
from pydantic import BaseModel


class OrganizationLogOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    details: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

