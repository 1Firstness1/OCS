import uuid
import pytest
from app.routers.logs import get_organization_logs, admin_get_org_logs
from app.models.user import PlatformRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_audit_log, make_member, make_user


@pytest.mark.asyncio
async def test_get_organization_logs_returns_items():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id, role="moderator")
    log = make_audit_log(user_id=user.id, organization_id=org_id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(all_rows=[(log, "User")]),
    ])
    result = await get_organization_logs(org_id=org_id, search="", current_user=user, db=db)
    assert len(result) == 1
    assert result[0].action == log.action


@pytest.mark.asyncio
async def test_admin_get_org_logs_returns_items():
    org_id = uuid.uuid4()
    admin = make_user(platform_role=PlatformRole.ADMIN)
    log = make_audit_log(user_id=admin.id, organization_id=org_id)
    db = FakeAsyncSession(results=[FakeResult(all_rows=[(log, "Admin")])])
    result = await admin_get_org_logs(org_id=org_id, search="", current_user=admin, db=db)
    assert result[0]["action"] == log.action

