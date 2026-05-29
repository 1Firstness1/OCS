import uuid
from datetime import datetime, date
from pydantic import BaseModel
from app.models.absence import AbsenceType, AbsenceStatus


class AbsenceCreate(BaseModel):
    absence_type: AbsenceType
    start_date: date
    end_date: date
    reason: str | None = None


class AbsenceOut(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    absence_type: AbsenceType
    status: AbsenceStatus
    start_date: date
    end_date: date
    reason: str | None
    approved_by: uuid.UUID | None
    created_at: datetime
    user_name: str | None = None

    class Config:
        from_attributes = True


class AbsenceApprove(BaseModel):
    status: AbsenceStatus
