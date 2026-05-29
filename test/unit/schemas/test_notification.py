from app.schemas.notification import NotificationOut
from test.factories import make_notification
import uuid


def test_notification_out_from_model():
    user_id = uuid.uuid4()
    note = make_notification(user_id=user_id)
    result = NotificationOut.model_validate(note)
    assert result.id == note.id
    assert result.title == note.title

