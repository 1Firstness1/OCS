import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
from app.models.board import CardPriority


class ChecklistItemBase(BaseModel):
    text: str
    is_completed: bool = False
    position: int = 0


class ChecklistItemCreate(ChecklistItemBase):
    pass


class ChecklistItemUpdate(BaseModel):
    text: Optional[str] = None
    is_completed: Optional[bool] = None
    position: Optional[int] = None


class ChecklistItemOut(ChecklistItemBase):
    id: uuid.UUID
    card_id: uuid.UUID

    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentOut(CommentBase):
    id: uuid.UUID
    card_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime
    author_name: Optional[str] = None

    class Config:
        from_attributes = True


class LabelBase(BaseModel):
    name: str
    color: str


class LabelCreate(LabelBase):
    pass


class LabelOut(LabelBase):
    id: uuid.UUID
    board_id: uuid.UUID

    class Config:
        from_attributes = True


class CardBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: CardPriority = CardPriority.MEDIUM
    due_date: Optional[date] = None
    assignee_id: Optional[uuid.UUID] = None


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[CardPriority] = None
    due_date: Optional[date] = None
    assignee_id: Optional[uuid.UUID] = None


class CardMove(BaseModel):
    column_id: uuid.UUID
    position: int


class CardOut(CardBase):
    id: uuid.UUID
    board_id: uuid.UUID
    column_id: uuid.UUID
    position: int
    creator_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    labels: List[LabelOut] = []
    comments: List[CommentOut] = []
    checklist: List[ChecklistItemOut] = []

    class Config:
        from_attributes = True


class ColumnBase(BaseModel):
    title: str


class ColumnCreate(ColumnBase):
    pass


class ColumnUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[int] = None


class ColumnReorder(BaseModel):
    column_id: uuid.UUID
    position: int


class ColumnOut(ColumnBase):
    id: uuid.UUID
    board_id: uuid.UUID
    position: int
    is_confirmed: bool = False
    cards: List[CardOut] = []

    class Config:
        from_attributes = True


class BoardBase(BaseModel):
    name: str
    description: Optional[str] = None


class BoardCreate(BoardBase):
    pass


class BoardOut(BoardBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime
    columns: List[ColumnOut] = []
    labels: List[LabelOut] = []

    class Config:
        from_attributes = True