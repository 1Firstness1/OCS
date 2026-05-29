import uuid
import pytest
from fastapi import HTTPException
from app.routers.members import list_members, update_member, remove_member
from app.schemas.member import MemberUpdate
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_member, make_user


@pytest.mark.asyncio
async def test_list_members_returns_items():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    other_user = make_user(user_id=member.user_id, username="u2", email="u2@example.com", full_name="User Two")
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(all_rows=[(member, other_user)]),
    ])
    result = await list_members(org_id=org_id, current_user=user, db=db)
    assert len(result) == 1
    assert result[0].email == "u2@example.com"


@pytest.mark.asyncio
async def test_update_member_success():
    org_id = uuid.uuid4()
    user = make_user()
    actor = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    target = make_member(uuid.uuid4(), org_id)
    target_user = make_user(user_id=target.user_id, full_name="Target")
    db = FakeAsyncSession(results=[
        FakeResult(scalar=actor),
        FakeResult(scalar=target),
        FakeResult(scalar=target_user),
    ])
    data = MemberUpdate(position="Lead")
    result = await update_member(org_id=org_id, member_id=target.id, data=data, current_user=user, db=db)
    assert result.position == "Lead"


@pytest.mark.asyncio
async def test_remove_member_rejects_self():
    org_id = uuid.uuid4()
    user = make_user()
    actor = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=actor),
        FakeResult(scalar=actor),
    ])
    with pytest.raises(HTTPException) as exc:
        await remove_member(org_id=org_id, member_id=actor.id, current_user=user, db=db)
    assert exc.value.status_code == 400
