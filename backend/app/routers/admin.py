import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User, PlatformRole
from app.models.organization import Organization
from app.models.member import Member
from app.models.audit import AuditLog
from app.schemas.user import UserOut, UserAdminUpdate
from app.utils.auth import get_current_user
from app.utils.permissions import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(
    search: str = Query(default="", max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)
    query = select(User)
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(User.created_at.desc())
    result = await db.execute(query)
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    data: UserAdminUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="not_found")
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.email is not None:
        user.email = data.email
    if data.platform_role is not None:
        user.platform_role = data.platform_role
    if data.is_active is not None:
        user.is_active = data.is_active
    await db.flush()
    await db.refresh(user)

    audit = AuditLog(
        user_id=current_user.id,
        action="update_user",
        entity_type="user",
        entity_id=str(user_id),
        details=f"Updated fields: {data.model_dump(exclude_none=True)}",
    )
    db.add(audit)
    await db.flush()

    return UserOut.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="cannot_deactivate_self")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="not_found")
    user.is_active = False
    await db.flush()


@router.get("/organizations")
async def list_all_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)
    subq = (
        select(Member.organization_id, func.count(Member.id).label("cnt"))
        .group_by(Member.organization_id)
        .subquery()
    )
    result = await db.execute(
        select(Organization, func.coalesce(subq.c.cnt, 0), User.full_name)
        .outerjoin(subq, subq.c.organization_id == Organization.id)
        .join(User, User.id == Organization.owner_id)
        .order_by(Organization.created_at.desc())
    )
    orgs = []
    for org, count, owner_name in result.all():
        orgs.append({
            "id": str(org.id),
            "name": org.name,
            "description": org.description,
            "owner_id": str(org.owner_id),
            "owner_name": owner_name,
            "is_active": org.is_active,
            "created_at": org.created_at.isoformat(),
            "member_count": count,
        })
    return orgs


@router.get("/audit-log")
async def get_audit_log(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)
    result = await db.execute(
        select(AuditLog, User.full_name)
        .join(User, User.id == AuditLog.user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    )
    logs = []
    for log, user_name in result.all():
        logs.append({
            "id": str(log.id),
            "user_name": user_name,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        })
    return logs


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)
    users_count = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
    orgs_count = (await db.execute(select(func.count(Organization.id)))).scalar()
    active_orgs = (await db.execute(select(func.count(Organization.id)).where(Organization.is_active == True))).scalar()
    return {
        "total_users": users_count,
        "active_users": active_users,
        "total_organizations": orgs_count,
        "active_organizations": active_orgs,
    }


@router.delete("/organizations/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="not_found")
    org.is_active = False
    await db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action="delete_organization",
        entity_type="organization",
        entity_id=str(org_id),
        details=f"Organization {org.name} deactivated",
    )
    db.add(audit)
    await db.flush()