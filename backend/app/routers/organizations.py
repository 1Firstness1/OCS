import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.member import Member, OrgRole
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationOut
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator
from app.utils.audit import log_action

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = Organization(
        name=data.name,
        description=data.description,
        category=data.category,
        data=data.data,
        owner_id=current_user.id,
    )
    db.add(org)
    await db.flush()

    member = Member(user_id=current_user.id, organization_id=org.id, role=OrgRole.MODERATOR)
    db.add(member)
    await db.flush()
    await db.refresh(org)

    await log_action(
        db, current_user.id, org.id,
        "Создание организации", "Организация", str(org.id),
        f"Организация '{org.name}' создана"
    )

    return OrganizationOut(
        id=org.id,
        name=org.name,
        description=org.description,
        category=org.category,
        data=org.data,
        owner_id=org.owner_id,
        is_active=org.is_active,
        created_at=org.created_at,
        member_count=1,
    )


@router.get("/", response_model=list[OrganizationOut])
async def list_my_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subq = (
        select(Member.organization_id, func.count(Member.id).label("cnt"))
        .group_by(Member.organization_id)
        .subquery()
    )
    result = await db.execute(
        select(Organization, func.coalesce(subq.c.cnt, 0))
        .join(Member, Member.organization_id == Organization.id)
        .outerjoin(subq, subq.c.organization_id == Organization.id)
        .where(Member.user_id == current_user.id, Organization.is_active == True)
    )
    orgs = []
    for org, count in result.all():
        orgs.append(
            OrganizationOut(
                id=org.id,
                name=org.name,
                description=org.description,
                category=org.category,
                data=org.data,
                owner_id=org.owner_id,
                is_active=org.is_active,
                created_at=org.created_at,
                member_count=count,
            )
        )
    return orgs


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="not_found")

    count_result = await db.execute(
        select(func.count(Member.id)).where(Member.organization_id == org_id)
    )
    count = count_result.scalar()

    return OrganizationOut(
        id=org.id,
        name=org.name,
        description=org.description,
        category=org.category,
        data=org.data,
        owner_id=org.owner_id,
        is_active=org.is_active,
        created_at=org.created_at,
        member_count=count,
    )


@router.put("/{org_id}", response_model=OrganizationOut)
async def update_organization(
    org_id: uuid.UUID,
    data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(member)

    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="not_found")

    if data.name is not None:
        org.name = data.name
    if data.description is not None:
        org.description = data.description
    if data.category is not None:
        org.category = data.category
    if data.data is not None:
        org.data = data.data

    await db.flush()
    await db.refresh(org)

    await log_action(
        db, current_user.id, org.id,
        "Обновление организации", "Организация", str(org.id),
        f"Обновлены настройки организации '{org.name}'"
    )

    count_result = await db.execute(
        select(func.count(Member.id)).where(Member.organization_id == org_id)
    )
    count = count_result.scalar()

    return OrganizationOut(
        id=org.id,
        name=org.name,
        description=org.description,
        category=org.category,
        data=org.data,
        owner_id=org.owner_id,
        is_active=org.is_active,
        created_at=org.created_at,
        member_count=count,
    )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="not_found")
    if org.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="owner_required")
    org.is_active = False
    
    await log_action(
        db, current_user.id, org.id,
        "Удаление организации", "Организация", str(org.id),
        f"Организация '{org.name}' деактивирована"
    )
    
    await db.flush()
