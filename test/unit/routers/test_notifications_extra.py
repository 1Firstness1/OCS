import pytest
from app.routers.notifications import list_notifications
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_notification, make_user


@pytest.mark.asyncio
async def test_list_notifications_unread_only():
    user = make_user()
    note = make_notification(user_id=user.id)
    db = FakeAsyncSession(results=[FakeResult(scalars=[note])])
    result = await list_notifications(current_user=user, db=db, unread_only=True)
    assert result[0].id == note.id

