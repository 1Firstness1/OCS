import uuid
import pytest
from fastapi import HTTPException
from app.routers.organizations import get_organization
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_member, make_organization, make_user


@pytest.mark.asyncio
async def test_get_organization_returns_member_count():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    org = make_organization(owner_id=user.id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=org),
        FakeResult(scalar=5),
    ])
    result = await get_organization(org_id=org_id, current_user=user, db=db)
    assert result.member_count == 5

