from app.schemas.logs import OrganizationLogOut
from test.factories import make_audit_log
import uuid


def test_organization_log_out_from_model():
    user_id = uuid.uuid4()
    log = make_audit_log(user_id=user_id)
    result = OrganizationLogOut.model_validate(log)
    assert result.user_id == user_id
    assert result.action == log.action

