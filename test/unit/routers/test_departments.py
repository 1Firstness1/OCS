import uuid
import pytest
from types import SimpleNamespace
from fastapi import HTTPException
from app.routers.departments import (
    create_department,
    list_departments,
    update_department,
    list_department_members,
)
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_department, make_member, make_user


@pytest.mark.asyncio
async def test_create_department_success():
    org_id = uuid.uuid4()
    user = make_user()
    actor = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[FakeResult(scalar=actor)])
    data = DepartmentCreate(name="HR", description=None)
    result = await create_department(org_id=org_id, data=data, current_user=user, db=db)
    assert result.name == "HR"


@pytest.mark.asyncio
async def test_list_departments_returns_items():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    dept = make_department(organization_id=org_id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(all_rows=[(dept, 2)]),
    ])
    result = await list_departments(org_id=org_id, current_user=user, db=db)
    assert len(result) == 1
    assert result[0].member_count == 2


@pytest.mark.asyncio
async def test_update_department_not_found():
    org_id = uuid.uuid4()
    user = make_user()
    actor = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=actor),
        FakeResult(scalar=None),
    ])
    data = DepartmentUpdate(name="New")
    with pytest.raises(HTTPException) as exc:
        await update_department(org_id=org_id, dept_id=uuid.uuid4(), data=data, current_user=user, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_department_members_populates_user_fields():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    other = make_member(uuid.uuid4(), org_id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalars=[other]),
        FakeResult(all_rows=[SimpleNamespace(id=other.user_id, full_name="Name", email="n@example.com")]),
    ])
    result = await list_department_members(org_id=org_id, dept_id=uuid.uuid4(), current_user=user, db=db)
    assert result[0].full_name == "Name"
