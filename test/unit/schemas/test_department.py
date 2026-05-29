from app.schemas.department import DepartmentOut
from test.factories import make_department
import uuid


def test_department_out_from_model():
    org_id = uuid.uuid4()
    dept = make_department(organization_id=org_id)
    result = DepartmentOut.model_validate(dept)
    assert result.organization_id == org_id
    assert result.name == dept.name

