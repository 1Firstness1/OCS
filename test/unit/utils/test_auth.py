import uuid
import pytest
from jose import jwt
from fastapi import HTTPException
from app.config import settings
from app.utils.auth import create_access_token, get_current_user
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_user


@pytest.mark.asyncio
async def test_create_access_token_has_sub_and_exp():
    token = create_access_token({"sub": "user-id"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "user-id"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_get_current_user_returns_user():
    user = make_user(user_id=uuid.uuid4())
    token = create_access_token({"sub": str(user.id)})
    db = FakeAsyncSession(results=[FakeResult(scalar=user)])
    result = await get_current_user(token=token, db=db)
    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_rejects_inactive_user():
    user = make_user(user_id=uuid.uuid4(), is_active=False)
    token = create_access_token({"sub": str(user.id)})
    db = FakeAsyncSession(results=[FakeResult(scalar=user)])
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=db)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_bad_token():
    db = FakeAsyncSession(results=[FakeResult(scalar=None)])
    with pytest.raises(HTTPException) as exc:
        await get_current_user(token="bad-token", db=db)
    assert exc.value.status_code == 401

