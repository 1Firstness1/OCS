import uuid
from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID | None = None
    title: str
    message: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
