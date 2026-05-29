import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class OrganizationCategory(str, enum.Enum):
    IT = "it"
    MARKETING = "marketing"
    HR = "hr"
    FINANCE = "finance"
    SALES = "sales"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    NONPROFIT = "nonprofit"
    OTHER = "other"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    category: Mapped[OrganizationCategory] = mapped_column(
        SAEnum(OrganizationCategory), default=OrganizationCategory.OTHER, nullable=False
    )
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("Member", back_populates="organization", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    chat_channels = relationship("ChatChannel", back_populates="organization", cascade="all, delete-orphan")
    finance_records = relationship("FinanceRecord", back_populates="organization", cascade="all, delete-orphan")
    absences = relationship("Absence", back_populates="organization", cascade="all, delete-orphan")
    boards = relationship("Board", back_populates="organization", cascade="all, delete-orphan")