from app.schemas.absence import AbsenceOut
from test.factories import make_absence
import uuid


def test_absence_out_from_model():
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    absence = make_absence(organization_id=org_id, user_id=user_id)
    result = AbsenceOut.model_validate(absence)
    assert result.id == absence.id
    assert result.user_id == user_id

