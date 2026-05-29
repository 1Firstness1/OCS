import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.absence import Absence, AbsenceStatus
from app.schemas.absence import AbsenceCreate, AbsenceOut, AbsenceApprove
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator

router = APIRouter(prefix="/api/organizations/{org_id}/absences", tags=["absences"])


@router.post("/", response_model=AbsenceOut, status_code=status.HTTP_201_CREATED)
async def create_absence(
    org_id: uuid.UUID,
    data: AbsenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    if data.start_date > data.end_date:
        raise HTTPException(status_code=400, detail="invalid_dates")
    absence = Absence(
        organization_id=org_id, user_id=current_user.id,
        absence_type=data.absence_type, start_date=data.start_date,
        end_date=data.end_date, reason=data.reason,
    )
    db.add(absence)
    await db.flush()
    await db.refresh(absence)
    return AbsenceOut(
        id=absence.id, organization_id=absence.organization_id,
        user_id=absence.user_id, absence_type=absence.absence_type,
        status=absence.status, start_date=absence.start_date,
        end_date=absence.end_date, reason=absence.reason,
        approved_by=absence.approved_by, created_at=absence.created_at,
        user_name=current_user.full_name,
    )


@router.get("/", response_model=list[AbsenceOut])
async def list_absences(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    result = await db.execute(
        select(Absence, User)
        .join(User, User.id == Absence.user_id)
        .where(Absence.organization_id == org_id)
        .order_by(Absence.start_date.desc())
    )
    return [
        AbsenceOut(
            id=a.id, organization_id=a.organization_id,
            user_id=a.user_id, absence_type=a.absence_type,
            status=a.status, start_date=a.start_date,
            end_date=a.end_date, reason=a.reason,
            approved_by=a.approved_by, created_at=a.created_at,
            user_name=u.full_name,
        )
        for a, u in result.all()
    ]


@router.put("/{absence_id}/approve", response_model=AbsenceOut)
async def approve_absence(
    org_id: uuid.UUID,
    absence_id: uuid.UUID,
    data: AbsenceApprove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)

    result = await db.execute(
        select(Absence).where(Absence.id == absence_id, Absence.organization_id == org_id)
    )
    absence = result.scalar_one_or_none()
    if not absence:
        raise HTTPException(status_code=404, detail="not_found")
    if absence.status != AbsenceStatus.PENDING:
        raise HTTPException(status_code=400, detail="already_processed")

    absence.status = data.status
    absence.approved_by = current_user.id
    await db.flush()
    await db.refresh(absence)

    user_result = await db.execute(select(User).where(User.id == absence.user_id))
    user = user_result.scalar_one()

    return AbsenceOut(
        id=absence.id, organization_id=absence.organization_id,
        user_id=absence.user_id, absence_type=absence.absence_type,
        status=absence.status, start_date=absence.start_date,
        end_date=absence.end_date, reason=absence.reason,
        approved_by=absence.approved_by, created_at=absence.created_at,
        user_name=user.full_name,
    )
