import uuid
import pytest
from app.routers.finance import create_record, list_records, approve_record
from app.schemas.finance import FinanceCreate, FinanceApprove
from app.models.finance import FinanceStatus
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_finance_record, make_member, make_user


@pytest.mark.asyncio
async def test_create_record_success():
    org_id = uuid.uuid4()
    user = make_user(full_name="User")
    member = make_member(user.id, org_id)
    data = FinanceCreate(title="T", description=None, amount=make_finance_record(org_id, user.id).amount, category=make_finance_record(org_id, user.id).category)
    db = FakeAsyncSession(results=[FakeResult(scalar=member)])
    result = await create_record(org_id=org_id, data=data, current_user=user, db=db)
    assert result.creator_name == "User"


@pytest.mark.asyncio
async def test_list_records_returns_items():
    org_id = uuid.uuid4()
    user = make_user(full_name="User")
    member = make_member(user.id, org_id)
    record = make_finance_record(org_id, user.id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(all_rows=[(record, user)]),
    ])
    result = await list_records(org_id=org_id, current_user=user, db=db)
    assert len(result) == 1
    assert result[0].id == record.id


@pytest.mark.asyncio
async def test_approve_record_updates_status():
    org_id = uuid.uuid4()
    user = make_user(full_name="Moderator")
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    record = make_finance_record(org_id, uuid.uuid4())
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=record),
        FakeResult(scalar=make_user(full_name="Creator")),
    ])
    data = FinanceApprove(status=FinanceStatus.APPROVED)
    result = await approve_record(org_id=org_id, record_id=record.id, data=data, current_user=user, db=db)
    assert result.status == FinanceStatus.APPROVED
