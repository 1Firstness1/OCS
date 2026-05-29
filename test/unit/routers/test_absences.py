import uuid
from datetime import date, timedelta
import pytest
from fastapi import HTTPException
from app.routers.absences import create_absence, list_absences, approve_absence
from app.schemas.absence import AbsenceCreate, AbsenceApprove
from app.models.absence import AbsenceStatus
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_absence, make_member, make_user


@pytest.mark.asyncio
async def test_create_absence_rejects_invalid_dates():
    user = make_user()
    db = FakeAsyncSession(results=[FakeResult(scalar=make_member(user.id, uuid.uuid4()))])
    data = AbsenceCreate(
        absence_type=make_absence(uuid.uuid4(), user.id).absence_type,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today(),
        reason=None,
    )
    with pytest.raises(HTTPException) as exc:
        await create_absence(org_id=uuid.uuid4(), data=data, current_user=user, db=db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_absence_success():
    org_id = uuid.uuid4()
    user = make_user(full_name="User")
    member = make_member(user.id, org_id)
    db = FakeAsyncSession(results=[FakeResult(scalar=member)])
    data = AbsenceCreate(
        absence_type=make_absence(org_id, user.id).absence_type,
        start_date=date.today(),
        end_date=date.today(),
        reason=None,
    )
    result = await create_absence(org_id=org_id, data=data, current_user=user, db=db)
    assert result.user_name == "User"


@pytest.mark.asyncio
async def test_list_absences_returns_items():
    org_id = uuid.uuid4()
    user = make_user(full_name="User")
    member = make_member(user.id, org_id)
    absence = make_absence(org_id, user.id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(all_rows=[(absence, user)]),
    ])
    result = await list_absences(org_id=org_id, current_user=user, db=db)
    assert len(result) == 1
    assert result[0].id == absence.id


@pytest.mark.asyncio
async def test_approve_absence_updates_status():
    org_id = uuid.uuid4()
    user = make_user(full_name="Moderator")
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    absence = make_absence(org_id, uuid.uuid4())
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=absence),
        FakeResult(scalar=make_user(full_name="Requester")),
    ])
    data = AbsenceApprove(status=AbsenceStatus.APPROVED)
    result = await approve_absence(org_id=org_id, absence_id=absence.id, data=data, current_user=user, db=db)
    assert result.status == AbsenceStatus.APPROVED

