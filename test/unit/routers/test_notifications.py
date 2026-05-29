import uuid
import pytest
from app.routers.notifications import list_notifications, mark_notification_read, mark_all_read
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_notification, make_user


@pytest.mark.asyncio
async def test_list_notifications_returns_items():
    user = make_user()
    note = make_notification(user_id=user.id)
    db = FakeAsyncSession(results=[FakeResult(scalars=[note])])
    result = await list_notifications(current_user=user, db=db)
    assert len(result) == 1
    assert result[0].id == note.id


@pytest.mark.asyncio
async def test_mark_notification_read_returns_ok():
    user = make_user()
    db = FakeAsyncSession(strict=False)
    result = await mark_notification_read(notification_id=uuid.uuid4(), current_user=user, db=db)
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_mark_all_read_returns_ok():
    user = make_user()
    db = FakeAsyncSession(strict=False)
    result = await mark_all_read(current_user=user, db=db)
    assert result == {"status": "ok"}

