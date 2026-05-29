import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class PlatformRole(str, enum.Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform_role: Mapped[PlatformRole] = mapped_column(SAEnum(PlatformRole), default=PlatformRole.USER, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    memberships = relationship("Member", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("Invitation", back_populates="inviter", foreign_keys="Invitation.inviter_id")
    chat_messages = relationship("ChatMessage", back_populates="author", foreign_keys="ChatMessage.author_id", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    card_comments = relationship("CardComment", back_populates="author", cascade="all, delete-orphan")
    created_boards = relationship("Board", back_populates="creator", foreign_keys="Board.created_by", cascade="all, delete-orphan")
    assigned_cards = relationship("Card", back_populates="assignee", foreign_keys="Card.assignee_id")
    created_cards = relationship("Card", back_populates="creator", foreign_keys="Card.creator_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")