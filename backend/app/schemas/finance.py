import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.finance import FinanceStatus, FinanceCategory


class FinanceCreate(BaseModel):
    title: str
    description: str | None = None
    amount: Decimal
    category: FinanceCategory


class FinanceOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by: uuid.UUID
    approved_by: uuid.UUID | None
    title: str
    description: str | None
    amount: Decimal
    category: FinanceCategory
    status: FinanceStatus
    created_at: datetime
    creator_name: str | None = None

    class Config:
        from_attributes = True


class FinanceApprove(BaseModel):
    status: FinanceStatus
