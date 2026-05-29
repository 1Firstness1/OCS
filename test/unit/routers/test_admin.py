import uuid
import pytest
from fastapi import HTTPException
from app.routers.admin import (
    list_users,
    update_user,
    deactivate_user,
    list_all_organizations,
    get_stats,
    admin_delete_organization,
)
from app.schemas.user import UserAdminUpdate
from app.models.user import PlatformRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_user, make_organization


@pytest.mark.asyncio
async def test_list_users_returns_items():
    admin = make_user(platform_role=PlatformRole.ADMIN)
    user = make_user(username="u2", email="u2@example.com")
    db = FakeAsyncSession(results=[FakeResult(scalars=[user])])
    result = await list_users(search="", current_user=admin, db=db)
    assert len(result) == 1
    assert result[0].email == "u2@example.com"


@pytest.mark.asyncio
async def test_update_user_not_found():
    admin = make_user(platform_role=PlatformRole.ADMIN)
    db = FakeAsyncSession(results=[FakeResult(scalar=None)])
    with pytest.raises(HTTPException) as exc:
        await update_user(user_id=uuid.uuid4(), data=UserAdminUpdate(full_name="X"), current_user=admin, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_user_rejects_self():
    admin = make_user(platform_role=PlatformRole.ADMIN)
    db = FakeAsyncSession()
    with pytest.raises(HTTPException) as exc:
        await deactivate_user(user_id=admin.id, current_user=admin, db=db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_list_all_organizations_returns_items():
    admin = make_user(platform_role=PlatformRole.ADMIN)
    org = make_organization(owner_id=uuid.uuid4())
    db = FakeAsyncSession(results=[FakeResult(all_rows=[(org, 2, "Owner")])])
    result = await list_all_organizations(current_user=admin, db=db)
    assert result[0]["member_count"] == 2


@pytest.mark.asyncio
async def test_get_stats_counts():
    admin = make_user(platform_role=PlatformRole.ADMIN)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=10),
        FakeResult(scalar=7),
        FakeResult(scalar=5),
        FakeResult(scalar=4),
    ])
    result = await get_stats(current_user=admin, db=db)
    assert result["total_users"] == 10
    assert result["active_organizations"] == 4


@pytest.mark.asyncio
async def test_admin_delete_organization_marks_inactive():
    admin = make_user(platform_role=PlatformRole.ADMIN)
    org = make_organization(owner_id=uuid.uuid4())
    db = FakeAsyncSession(results=[FakeResult(scalar=org)])
    await admin_delete_organization(org_id=org.id, current_user=admin, db=db)
    assert org.is_active is False
    assert any(obj.__class__.__name__ == "AuditLog" for obj in db.added)

