import uuid
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.member import Member, OrgRole
from app.models.invitation import Invitation, InvitationStatus
from app.models.notification import Notification
from app.models.audit import AuditLog
from app.schemas.invitation import InvitationCreate, InvitationOut
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator

router = APIRouter(prefix="/api/organizations/{org_id}/invitations", tags=["invitations"])
user_invites_router = APIRouter(prefix="/api/invitations", tags=["invitations"])

INVITE_EXPIRY_DAYS = 7


@router.post("/", response_model=InvitationOut, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    org_id: uuid.UUID,
    data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    existing = await db.execute(
        select(Invitation).where(
            Invitation.organization_id == org_id,
            Invitation.email == data.email,
            Invitation.status == InvitationStatus.PENDING,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="invitation_already_sent")

    existing_member = await db.execute(
        select(Member)
        .join(User, User.id == Member.user_id)
        .where(Member.organization_id == org_id, User.email == data.email)
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="already_a_member")

    invite = Invitation(
        organization_id=org_id,
        inviter_id=current_user.id,
        email=data.email,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(invite)
    await db.flush()
    await db.refresh(invite)

    user_result = await db.execute(select(User).where(User.email == data.email))
    invited_user = user_result.scalar_one_or_none()
    if invited_user:
        db.add(
            Notification(
                user_id=invited_user.id,
                organization_id=org_id,
                title="Приглашение в организацию",
                message=f"Вас пригласили в организацию. Проверьте раздел приглашений.",
                entity_type="invitation",
                entity_id=str(invite.id),
            )
        )

    db.add(
        AuditLog(
            user_id=current_user.id,
            organization_id=org_id,
            action="create_invitation",
            entity_type="invitation",
            entity_id=str(invite.id),
            details=f"Invite sent to {data.email}",
        )
    )

    return InvitationOut.model_validate(invite)


@router.get("/", response_model=list[InvitationOut])
async def list_invitations(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(Invitation).where(Invitation.organization_id == org_id).order_by(Invitation.created_at.desc())
    )
    return [InvitationOut.model_validate(i) for i in result.scalars().all()]


@router.post("/{invite_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    org_id: uuid.UUID,
    invite_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(Invitation).where(Invitation.id == invite_id, Invitation.organization_id == org_id)
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="not_found")
    invite.status = InvitationStatus.EXPIRED
    await db.flush()


@router.post("/accept/{token}")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="invitation_not_found")
    if invite.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail="invitation_not_pending")
    if invite.expires_at < datetime.now(timezone.utc):
        invite.status = InvitationStatus.EXPIRED
        await db.flush()
        raise HTTPException(status_code=400, detail="invitation_expired")
    if invite.email != current_user.email:
        raise HTTPException(status_code=403, detail="email_mismatch")

    existing = await db.execute(
        select(Member).where(
            Member.user_id == current_user.id,
            Member.organization_id == invite.organization_id,
        )
    )
    if existing.scalar_one_or_none():
        invite.status = InvitationStatus.ACCEPTED
        await db.flush()
        return {"detail": "already_member"}

    member = Member(
        user_id=current_user.id,
        organization_id=invite.organization_id,
        role=OrgRole.EMPLOYEE,
    )
    db.add(member)
    invite.status = InvitationStatus.ACCEPTED
    await db.flush()

    db.add(
        AuditLog(
            user_id=current_user.id,
            organization_id=invite.organization_id,
            action="accept_invitation",
            entity_type="invitation",
            entity_id=str(invite.id),
            details="Invitation accepted",
        )
    )

    return {"detail": "accepted"}


@user_invites_router.get("/my-pending", response_model=list[InvitationOut])
async def my_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Invitation).where(
            Invitation.email == current_user.email,
            Invitation.status == InvitationStatus.PENDING,
        )
    )
    return [InvitationOut.model_validate(i) for i in result.scalars().all()]
