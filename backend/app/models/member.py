import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class OrgRole(str, enum.Enum):
    EMPLOYEE = "employee"
    MODERATOR = "moderator"


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("user_id", "organization_id", name="uq_member_user_org"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    role: Mapped[OrgRole] = mapped_column(SAEnum(OrgRole), default=OrgRole.EMPLOYEE, nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="members")
    department = relationship("Department", back_populates="members")
