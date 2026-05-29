import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, ForeignKey, Date, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class AbsenceType(str, enum.Enum):
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"
    BUSINESS_TRIP = "business_trip"
    REMOTE = "remote"
    OTHER = "other"


class AbsenceStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Absence(Base):
    __tablename__ = "absences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    absence_type: Mapped[AbsenceType] = mapped_column(SAEnum(AbsenceType), nullable=False)
    status: Mapped[AbsenceStatus] = mapped_column(SAEnum(AbsenceStatus), default=AbsenceStatus.PENDING, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="absences")
    user = relationship("User", foreign_keys=[user_id])
    approver = relationship("User", foreign_keys=[approved_by])
