import uuid
from app.schemas.finance import FinanceOut
from test.factories import make_finance_record


def test_finance_out_from_model():
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    record = make_finance_record(organization_id=org_id, created_by=user_id)
    result = FinanceOut.model_validate(record)
    assert result.id == record.id
    assert result.created_by == user_id
