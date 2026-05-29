import uuid
import pytest
from fastapi import HTTPException
from app.utils.permissions import get_member_or_fail, require_admin, require_moderator
from app.models.user import PlatformRole
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_member, make_user


@pytest.mark.asyncio
async def test_get_member_or_fail_returns_member():
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    member = make_member(user_id=user_id, organization_id=org_id)
    db = FakeAsyncSession(results=[FakeResult(scalar=member)])
    result = await get_member_or_fail(db=db, user_id=user_id, org_id=org_id)
    assert result.id == member.id


@pytest.mark.asyncio
async def test_get_member_or_fail_raises_for_missing_member():
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    db = FakeAsyncSession(results=[FakeResult(scalar=None)])
    with pytest.raises(HTTPException) as exc:
        await get_member_or_fail(db=db, user_id=user_id, org_id=org_id)
    assert exc.value.status_code == 403


def test_require_moderator_accepts_moderator():
    member = make_member(user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role=OrgRole.MODERATOR)
    require_moderator(member)


def test_require_moderator_rejects_employee():
    member = make_member(user_id=uuid.uuid4(), organization_id=uuid.uuid4(), role=OrgRole.EMPLOYEE)
    with pytest.raises(HTTPException) as exc:
        require_moderator(member)
    assert exc.value.status_code == 403


def test_require_admin_accepts_admin():
    user = make_user(platform_role=PlatformRole.ADMIN)
    require_admin(user)


def test_require_admin_rejects_user():
    user = make_user(platform_role=PlatformRole.USER)
    with pytest.raises(HTTPException) as exc:
        require_admin(user)
    assert exc.value.status_code == 403

