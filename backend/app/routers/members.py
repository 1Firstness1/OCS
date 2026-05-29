import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.member import Member
from app.schemas.member import MemberOut, MemberUpdate
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator
from app.utils.audit import log_action

router = APIRouter(prefix="/api/organizations/{org_id}/members", tags=["members"])


@router.get("/", response_model=list[MemberOut])
async def list_members(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    result = await db.execute(
        select(Member, User)
        .join(User, User.id == Member.user_id)
        .where(Member.organization_id == org_id)
    )
    members = []
    for m, u in result.all():
        members.append(
            MemberOut(
                id=m.id,
                user_id=m.user_id,
                organization_id=m.organization_id,
                department_id=m.department_id,
                role=m.role,
                position=m.position,
                joined_at=m.joined_at,
                username=u.username,
                full_name=u.full_name,
                email=u.email,
            )
        )
    return members


@router.put("/{member_id}", response_model=MemberOut)
async def update_member(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    data: MemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.organization_id == org_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="member_not_found")

    if data.role is not None:
        member.role = data.role
    if data.position is not None:
        member.position = data.position
    if data.department_id is not None:
        member.department_id = data.department_id

    await db.flush()
    await db.refresh(member)

    user_result = await db.execute(select(User).where(User.id == member.user_id))
    user = user_result.scalar_one()

    await log_action(
        db, current_user.id, org_id,
        "Изменение сотрудника", "Сотрудник", str(member.id),
        f"Обновлены данные сотрудника '{user.full_name}'"
    )

    return MemberOut(
        id=member.id,
        user_id=member.user_id,
        organization_id=member.organization_id,
        department_id=member.department_id,
        role=member.role,
        position=member.position,
        joined_at=member.joined_at,
        username=user.username,
        full_name=user.full_name,
        email=user.email,
    )


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(Member).where(Member.id == member_id, Member.organization_id == org_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="member_not_found")
    if member.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="cannot_remove_self")

    await db.delete(member)
    
    user_result = await db.execute(select(User).where(User.id == member.user_id))
    user = user_result.scalar_one_or_none()
    user_name = user.full_name if user else "Неизвестно"
    
    await log_action(
        db, current_user.id, org_id,
        "Удаление сотрудника", "Сотрудник", str(member.id),
        f"Сотрудник '{user_name}' исключен из организации"
    )
    
    await db.flush()
