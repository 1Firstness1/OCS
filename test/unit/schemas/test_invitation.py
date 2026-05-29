from app.schemas.invitation import InvitationOut
from test.factories import make_invitation
import uuid


def test_invitation_out_from_model():
    org_id = uuid.uuid4()
    inviter_id = uuid.uuid4()
    invite = make_invitation(organization_id=org_id, inviter_id=inviter_id)
    result = InvitationOut.model_validate(invite)
    assert result.organization_id == org_id
    assert result.inviter_id == inviter_id

