import uuid
import pytest
from app.utils.audit import log_action
from app.models.audit import AuditLog
from test.fakes import FakeAsyncSession


@pytest.mark.asyncio
async def test_log_action_adds_audit_log():
    db = FakeAsyncSession()
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()

    await log_action(
        db=db,
        user_id=user_id,
        organization_id=org_id,
        action="create",
        entity_type="organization",
        entity_id="org-1",
        details="created",
    )

    assert len(db.added) == 1
    log = db.added[0]
    assert isinstance(log, AuditLog)
    assert log.user_id == user_id
    assert log.organization_id == org_id
    assert log.action == "create"

