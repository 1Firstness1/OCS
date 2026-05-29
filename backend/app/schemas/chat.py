import uuid
from datetime import datetime
from pydantic import BaseModel


class ChannelCreate(BaseModel):
    name: str
    description: str | None = None


class ChannelOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: uuid.UUID
    channel_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    is_deleted: bool
    created_at: datetime
    author_name: str | None = None

    class Config:
        from_attributes = True
