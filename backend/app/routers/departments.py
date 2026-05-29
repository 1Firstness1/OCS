import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.department import Department
from app.models.member import Member
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentOut
from app.schemas.member import MemberOut
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator
from app.utils.audit import log_action

router = APIRouter(prefix="/api/organizations/{org_id}/departments", tags=["departments"])


@router.post("/", response_model=DepartmentOut, status_code=status.HTTP_201_CREATED)
async def create_department(
    org_id: uuid.UUID,
    data: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    dept = Department(organization_id=org_id, name=data.name, description=data.description)
    db.add(dept)
    await db.flush()
    await db.refresh(dept)

    await log_action(
        db, current_user.id, org_id,
        "Создание отдела", "Отдел", str(dept.id),
        f"Отдел '{dept.name}' создан"
    )

    return DepartmentOut(
        id=dept.id,
        organization_id=dept.organization_id,
        name=dept.name,
        description=dept.description,
        created_at=dept.created_at,
        member_count=0,
    )


@router.get("/", response_model=list[DepartmentOut])
async def list_departments(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    subq = (
        select(Member.department_id, func.count(Member.id).label("cnt"))
        .where(Member.organization_id == org_id, Member.department_id.isnot(None))
        .group_by(Member.department_id)
        .subquery()
    )

    result = await db.execute(
        select(Department, func.coalesce(subq.c.cnt, 0))
        .outerjoin(subq, subq.c.department_id == Department.id)
        .where(Department.organization_id == org_id)
    )

    return [
        DepartmentOut(
            id=d.id,
            organization_id=d.organization_id,
            name=d.name,
            description=d.description,
            created_at=d.created_at,
            member_count=c,
        )
        for d, c in result.all()
    ]


@router.put("/{dept_id}", response_model=DepartmentOut)
async def update_department(
    org_id: uuid.UUID,
    dept_id: uuid.UUID,
    data: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="not_found")

    if data.name is not None:
        dept.name = data.name
    if data.description is not None:
        dept.description = data.description

    await db.flush()
    await db.refresh(dept)

    await log_action(
        db, current_user.id, org_id,
        "Обновление отдела", "Отдел", str(dept.id),
        f"Обновлены настройки отдела '{dept.name}'"
    )

    count_result = await db.execute(
        select(func.count(Member.id)).where(Member.department_id == dept_id)
    )
    count = count_result.scalar()

    return DepartmentOut(
        id=dept.id,
        organization_id=dept.organization_id,
        name=dept.name,
        description=dept.description,
        created_at=dept.created_at,
        member_count=count,
    )


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    org_id: uuid.UUID,
    dept_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="not_found")

    await db.execute(
        select(Member).where(Member.department_id == dept_id)
    )
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(Member).where(Member.department_id == dept_id).values(department_id=None)
    )

    await db.delete(dept)
    
    await log_action(
        db, current_user.id, org_id,
        "Удаление отдела", "Отдел", str(dept.id),
        f"Отдел '{dept.name}' удален"
    )
    
    await db.flush()


@router.get("/{dept_id}/members", response_model=list[MemberOut])
async def list_department_members(
    org_id: uuid.UUID,
    dept_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(
        select(Member)
        .where(Member.department_id == dept_id, Member.organization_id == org_id)
        .order_by(Member.joined_at.desc())
    )
    members = result.scalars().all()
    
    # We need to fetch user names
    user_ids = [m.user_id for m in members]
    if user_ids:
        users_res = await db.execute(select(User.id, User.full_name, User.email).where(User.id.in_(user_ids)))
        users_map = {row.id: {"full_name": row.full_name, "email": row.email} for row in users_res.all()}
        for m in members:
            u_info = users_map.get(m.user_id, {})
            m.full_name = u_info.get("full_name")
            m.email = u_info.get("email")

    return members
