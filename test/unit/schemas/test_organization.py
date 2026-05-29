from app.schemas.organization import OrganizationOut
from test.factories import make_organization
import uuid


def test_organization_out_from_model():
    org = make_organization(owner_id=uuid.uuid4())
    result = OrganizationOut.model_validate(org)
    assert result.id == org.id
    assert result.name == org.name
