import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.finance import FinanceRecord, FinanceStatus
from app.schemas.finance import FinanceCreate, FinanceOut, FinanceApprove
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator

router = APIRouter(prefix="/api/organizations/{org_id}/finance", tags=["finance"])


@router.post("/", response_model=FinanceOut, status_code=status.HTTP_201_CREATED)
async def create_record(
    org_id: uuid.UUID,
    data: FinanceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    record = FinanceRecord(
        organization_id=org_id, created_by=current_user.id,
        title=data.title, description=data.description,
        amount=data.amount, category=data.category,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return FinanceOut(
        id=record.id, organization_id=record.organization_id,
        created_by=record.created_by, approved_by=record.approved_by,
        title=record.title, description=record.description,
        amount=record.amount, category=record.category,
        status=record.status, created_at=record.created_at,
        creator_name=current_user.full_name,
    )


@router.get("/", response_model=list[FinanceOut])
async def list_records(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    result = await db.execute(
        select(FinanceRecord, User)
        .join(User, User.id == FinanceRecord.created_by)
        .where(FinanceRecord.organization_id == org_id)
        .order_by(FinanceRecord.created_at.desc())
    )
    return [
        FinanceOut(
            id=r.id, organization_id=r.organization_id,
            created_by=r.created_by, approved_by=r.approved_by,
            title=r.title, description=r.description,
            amount=r.amount, category=r.category,
            status=r.status, created_at=r.created_at,
            creator_name=u.full_name,
        )
        for r, u in result.all()
    ]


@router.put("/{record_id}/approve", response_model=FinanceOut)
async def approve_record(
    org_id: uuid.UUID,
    record_id: uuid.UUID,
    data: FinanceApprove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(FinanceRecord).where(FinanceRecord.id == record_id, FinanceRecord.organization_id == org_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="not_found")
    if record.status != FinanceStatus.PENDING:
        raise HTTPException(status_code=400, detail="already_processed")

    record.status = data.status
    record.approved_by = current_user.id
    await db.flush()
    await db.refresh(record)

    user_result = await db.execute(select(User).where(User.id == record.created_by))
    creator = user_result.scalar_one()

    return FinanceOut(
        id=record.id, organization_id=record.organization_id,
        created_by=record.created_by, approved_by=record.approved_by,
        title=record.title, description=record.description,
        amount=record.amount, category=record.category,
        status=record.status, created_at=record.created_at,
        creator_name=creator.full_name,
    )
