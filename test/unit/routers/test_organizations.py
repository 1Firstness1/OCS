import uuid
import pytest
from fastapi import HTTPException
from app.routers.organizations import (
    create_organization,
    list_my_organizations,
    get_organization,
    update_organization,
    delete_organization,
)
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_member, make_organization, make_user


@pytest.mark.asyncio
async def test_create_organization_adds_member_and_logs(mocker):
    user = make_user()
    db = FakeAsyncSession()
    log_mock = mocker.AsyncMock()
    mocker.patch("app.routers.organizations.log_action", log_mock)
    data = OrganizationCreate(name="Org", description=None, data=None)
    result = await create_organization(data=data, current_user=user, db=db)
    assert result.member_count == 1
    assert any(obj.__class__.__name__ == "Organization" for obj in db.added)
    assert any(obj.__class__.__name__ == "Member" for obj in db.added)
    log_mock.assert_called_once()


@pytest.mark.asyncio
async def test_list_my_organizations_returns_items():
    user = make_user()
    org = make_organization(owner_id=user.id)
    db = FakeAsyncSession(results=[FakeResult(all_rows=[(org, 3)])])
    result = await list_my_organizations(current_user=user, db=db)
    assert len(result) == 1
    assert result[0].member_count == 3


@pytest.mark.asyncio
async def test_get_organization_not_found():
    user = make_user()
    member = make_member(user.id, uuid.uuid4())
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=None),
    ])
    with pytest.raises(HTTPException) as exc:
        await get_organization(org_id=uuid.uuid4(), current_user=user, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_organization_updates_fields(mocker):
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    org = make_organization(owner_id=user.id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=org),
        FakeResult(scalar=2),
    ])
    mocker.patch("app.routers.organizations.log_action", mocker.AsyncMock())
    data = OrganizationUpdate(name="New")
    result = await update_organization(org_id=org_id, data=data, current_user=user, db=db)
    assert result.name == "New"
    assert result.member_count == 2


@pytest.mark.asyncio
async def test_delete_organization_requires_owner():
    org_id = uuid.uuid4()
    user = make_user()
    org = make_organization(owner_id=uuid.uuid4())
    db = FakeAsyncSession(results=[FakeResult(scalar=org)])
    with pytest.raises(HTTPException) as exc:
        await delete_organization(org_id=org_id, current_user=user, db=db)
    assert exc.value.status_code == 403

