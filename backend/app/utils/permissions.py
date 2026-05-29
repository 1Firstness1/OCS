import uuid
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.member import Member, OrgRole
from app.models.user import User, PlatformRole


async def get_member_or_fail(
    db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID
) -> Member:
    result = await db.execute(
        select(Member).where(
            Member.user_id == user_id,
            Member.organization_id == org_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_a_member")
    return member


def require_moderator(member: Member):
    if member.role != OrgRole.MODERATOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="moderator_required")


def require_admin(user: User):
    if user.platform_role != PlatformRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")
