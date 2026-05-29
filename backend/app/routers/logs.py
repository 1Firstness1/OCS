import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.logs import OrganizationLogOut
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_admin

router = APIRouter(prefix="/api/organizations/{org_id}/logs", tags=["logs"])
admin_org_logs_router = APIRouter(prefix="/api/admin/organizations", tags=["admin"])


@router.get("", response_model=list[OrganizationLogOut])
async def get_organization_logs(
    org_id: uuid.UUID,
    search: str = Query(default="", max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)

    query = (
        select(AuditLog, User.full_name)
        .join(User, User.id == AuditLog.user_id)
        .where(AuditLog.organization_id == org_id)
    )

    # Employee sees only own actions; moderator sees all
    if member.role != "moderator":
        query = query.where(AuditLog.user_id == current_user.id)

    if search:
        query = query.where(
            or_(
                AuditLog.action.ilike(f"%{search}%"),
                AuditLog.entity_type.ilike(f"%{search}%"),
                AuditLog.details.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(AuditLog.created_at.desc()).limit(200)
    result = await db.execute(query)

    logs = []
    for log, user_name in result.all():
        logs.append(
            OrganizationLogOut(
                id=log.id,
                user_id=log.user_id,
                user_name=user_name,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.details,
                created_at=log.created_at,
            )
        )
    return logs


@admin_org_logs_router.get("/{org_id}/logs")
async def admin_get_org_logs(
    org_id: uuid.UUID,
    search: str = Query(default="", max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(current_user)

    query = (
        select(AuditLog, User.full_name)
        .join(User, User.id == AuditLog.user_id)
        .where(AuditLog.organization_id == org_id)
    )

    if search:
        query = query.where(
            or_(
                AuditLog.action.ilike(f"%{search}%"),
                AuditLog.entity_type.ilike(f"%{search}%"),
                AuditLog.details.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )

    query = query.order_by(AuditLog.created_at.desc()).limit(200)
    result = await db.execute(query)

    logs = []
    for log, user_name in result.all():
        logs.append({
            "id": str(log.id),
            "user_id": str(log.user_id),
            "user_name": user_name,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        })
    return logs
