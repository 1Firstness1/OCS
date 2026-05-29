from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.member import Member
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/users")
async def search_users(
    q: str = Query(min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User)
        .where(
            or_(
                User.username.ilike(f"%{q}%"),
                User.full_name.ilike(f"%{q}%"),
                User.email.ilike(f"%{q}%"),
            ),
            User.is_active == True,
        )
        .limit(20)
    )
    return [
        {"id": str(u.id), "username": u.username, "full_name": u.full_name, "email": u.email}
        for u in result.scalars().all()
    ]


@router.get("/organizations")
async def search_my_organizations(
    q: str = Query(min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Organization)
        .join(Member, Member.organization_id == Organization.id)
        .where(
            Member.user_id == current_user.id,
            Organization.is_active == True,
            Organization.name.ilike(f"%{q}%"),
        )
        .limit(20)
    )
    return [
        {"id": str(o.id), "name": o.name, "description": o.description}
        for o in result.scalars().all()
    ]
