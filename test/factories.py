import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from app.models.user import User, PlatformRole
from app.models.member import Member, OrgRole
from app.models.organization import Organization, OrganizationCategory
from app.models.absence import Absence, AbsenceType, AbsenceStatus
from app.models.finance import FinanceRecord, FinanceCategory, FinanceStatus
from app.models.department import Department
from app.models.invitation import Invitation, InvitationStatus
from app.models.notification import Notification
from app.models.chat import ChatChannel, ChatMessage
from app.models.audit import AuditLog
from app.models.board import (
    Board,
    BoardColumn,
    Card,
    CardPriority,
    CardLabel,
    CardLabelAssignment,
    CardComment,
    ChecklistItem,
)


def make_user(
    user_id=None,
    email="user@example.com",
    username="user",
    full_name="User Name",
    hashed_password="hashed",
    platform_role=PlatformRole.USER,
    is_active=True,
):
    return User(
        id=user_id or uuid.uuid4(),
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        platform_role=platform_role,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
    )


def make_member(user_id, organization_id, role=OrgRole.EMPLOYEE):
    return Member(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        role=role,
        joined_at=datetime.now(timezone.utc),
    )


def make_organization(owner_id, name="Org", category=OrganizationCategory.OTHER):
    return Organization(
        id=uuid.uuid4(),
        name=name,
        description=None,
        category=category,
        data=None,
        owner_id=owner_id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )


def make_absence(
    organization_id,
    user_id,
    absence_type=AbsenceType.VACATION,
    status=AbsenceStatus.PENDING,
    start_date=None,
    end_date=None,
):
    today = date.today()
    return Absence(
        id=uuid.uuid4(),
        organization_id=organization_id,
        user_id=user_id,
        absence_type=absence_type,
        status=status,
        start_date=start_date or today,
        end_date=end_date or today,
        reason=None,
        approved_by=None,
        created_at=datetime.now(timezone.utc),
    )


def make_finance_record(
    organization_id,
    created_by,
    title="Record",
    amount=Decimal("10.00"),
    category=FinanceCategory.EXPENSE,
    status=FinanceStatus.PENDING,
):
    return FinanceRecord(
        id=uuid.uuid4(),
        organization_id=organization_id,
        created_by=created_by,
        approved_by=None,
        title=title,
        description=None,
        amount=amount,
        category=category,
        status=status,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_department(organization_id, name="Dept"):
    return Department(
        id=uuid.uuid4(),
        organization_id=organization_id,
        name=name,
        description=None,
        created_at=datetime.now(timezone.utc),
    )


def make_invitation(
    organization_id,
    inviter_id,
    email="invitee@example.com",
    status=InvitationStatus.PENDING,
):
    return Invitation(
        id=uuid.uuid4(),
        organization_id=organization_id,
        inviter_id=inviter_id,
        email=email,
        status=status,
        token="token123",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )


def make_notification(user_id, organization_id=None, title="Notice"):
    return Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        title=title,
        message=None,
        entity_type=None,
        entity_id=None,
        is_read=False,
        created_at=datetime.now(timezone.utc),
    )


def make_chat_channel(organization_id, name="general"):
    return ChatChannel(
        id=uuid.uuid4(),
        organization_id=organization_id,
        name=name,
        description=None,
        created_at=datetime.now(timezone.utc),
    )


def make_chat_message(channel_id, author_id, content="Hi"):
    return ChatMessage(
        id=uuid.uuid4(),
        channel_id=channel_id,
        author_id=author_id,
        content=content,
        is_deleted=False,
        deleted_by=None,
        created_at=datetime.now(timezone.utc),
    )


def make_audit_log(user_id, organization_id=None, action="action"):
    return AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        entity_type="entity",
        entity_id=str(uuid.uuid4()),
        details=None,
        created_at=datetime.now(timezone.utc),
    )


def make_board(organization_id, created_by, name="Board"):
    return Board(
        id=uuid.uuid4(),
        organization_id=organization_id,
        name=name,
        description=None,
        created_by=created_by,
        created_at=datetime.now(timezone.utc),
    )


def make_board_column(board_id, title="Todo", position=0, is_confirmed=False):
    return BoardColumn(
        id=uuid.uuid4(),
        board_id=board_id,
        title=title,
        position=position,
        is_confirmed=is_confirmed,
    )


def make_card(board_id, column_id, creator_id, title="Card"):
    return Card(
        id=uuid.uuid4(),
        board_id=board_id,
        column_id=column_id,
        title=title,
        description=None,
        position=0,
        priority=CardPriority.MEDIUM,
        due_date=None,
        creator_id=creator_id,
        assignee_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_card_label(board_id, name="Label", color="#000000"):
    return CardLabel(
        id=uuid.uuid4(),
        board_id=board_id,
        name=name,
        color=color,
    )


def make_label_assignment(card_id, label_id):
    return CardLabelAssignment(
        id=uuid.uuid4(),
        card_id=card_id,
        label_id=label_id,
    )


def make_card_comment(card_id, author_id, content="Comment"):
    return CardComment(
        id=uuid.uuid4(),
        card_id=card_id,
        author_id=author_id,
        content=content,
        created_at=datetime.now(timezone.utc),
    )


def make_checklist_item(card_id, text="Item", position=0, is_completed=False):
    return ChecklistItem(
        id=uuid.uuid4(),
        card_id=card_id,
        text=text,
        is_completed=is_completed,
        position=position,
    )

