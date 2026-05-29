import uuid
import pytest
from types import SimpleNamespace
from fastapi import HTTPException
from app.routers.auth import register, login, update_me, reauth
from app.schemas.user import UserCreate, UserUpdate, ReauthRequest
from app.utils.security import verify_password, hash_password
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_user


@pytest.mark.asyncio
async def test_register_rejects_duplicate_user():
    existing_user = make_user()
    db = FakeAsyncSession(results=[FakeResult(scalar=existing_user)])
    data = UserCreate(
        email="user@example.com",
        username="user",
        password="secret",
        full_name="User Name",
    )
    with pytest.raises(HTTPException) as exc:
        await register(data=data, db=db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_register_creates_user_and_token():
    db = FakeAsyncSession(results=[FakeResult(scalar=None)])
    data = UserCreate(
        email="user@example.com",
        username="user",
        password="secret",
        full_name="User Name",
    )
    result = await register(data=data, db=db)
    assert result.access_token
    assert result.user.email == data.email
    assert len(db.added) == 1
    created_user = db.added[0]
    assert verify_password("secret", created_user.hashed_password) is True


@pytest.mark.asyncio
async def test_login_success():
    user = make_user(hashed_password=hash_password("secret"))
    db = FakeAsyncSession(results=[FakeResult(scalar=user)])
    form = SimpleNamespace(username=user.username, password="secret")
    result = await login(form=form, db=db)
    assert result.access_token
    assert result.user.id == user.id


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials():
    db = FakeAsyncSession(results=[FakeResult(scalar=None)])
    form = SimpleNamespace(username="missing", password="secret")
    with pytest.raises(HTTPException) as exc:
        await login(form=form, db=db)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_rejects_inactive_user():
    user = make_user(hashed_password=hash_password("secret"), is_active=False)
    db = FakeAsyncSession(results=[FakeResult(scalar=user)])
    form = SimpleNamespace(username=user.username, password="secret")
    with pytest.raises(HTTPException) as exc:
        await login(form=form, db=db)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_me_rejects_taken_email():
    current_user = make_user()
    db = FakeAsyncSession(results=[FakeResult(scalar=make_user())])
    data = UserUpdate(email="taken@example.com")
    with pytest.raises(HTTPException) as exc:
        await update_me(data=data, current_user=current_user, db=db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_update_me_updates_fields():
    current_user = make_user()
    db = FakeAsyncSession(results=[FakeResult(scalar=None)])
    data = UserUpdate(email="new@example.com", full_name="New Name")
    result = await update_me(data=data, current_user=current_user, db=db)
    assert result.email == "new@example.com"
    assert result.full_name == "New Name"


@pytest.mark.asyncio
async def test_reauth_accepts_valid_password():
    current_user = make_user(hashed_password=hash_password("secret"))
    data = ReauthRequest(password="secret")
    result = await reauth(data=data, current_user=current_user)
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_reauth_rejects_invalid_password():
    current_user = make_user(hashed_password=hash_password("secret"))
    data = ReauthRequest(password="bad")
    with pytest.raises(HTTPException) as exc:
        await reauth(data=data, current_user=current_user)
    assert exc.value.status_code == 401

