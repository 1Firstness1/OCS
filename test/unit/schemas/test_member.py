from app.schemas.member import MemberOut
from test.factories import make_member
import uuid


def test_member_out_from_model():
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    member = make_member(user_id=user_id, organization_id=org_id)
    result = MemberOut.model_validate(member)
    assert result.user_id == user_id
    assert result.organization_id == org_id

