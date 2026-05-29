import pytest
from app.routers.search import search_users, search_my_organizations
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_organization, make_user


@pytest.mark.asyncio
async def test_search_users_returns_items():
    user = make_user(username="john", email="john@example.com")
    db = FakeAsyncSession(results=[FakeResult(scalars=[user])])
    result = await search_users(q="jo", current_user=user, db=db)
    assert result[0]["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_search_my_organizations_returns_items():
    user = make_user()
    org = make_organization(owner_id=user.id, name="Org")
    db = FakeAsyncSession(results=[FakeResult(scalars=[org])])
    result = await search_my_organizations(q="Org", current_user=user, db=db)
    assert result[0]["name"] == "Org"

