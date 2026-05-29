from app.schemas.chat import ChannelOut, MessageOut
from test.factories import make_chat_channel, make_chat_message
import uuid


def test_channel_out_from_model():
    org_id = uuid.uuid4()
    channel = make_chat_channel(organization_id=org_id)
    result = ChannelOut.model_validate(channel)
    assert result.organization_id == org_id


def test_message_out_from_model():
    channel_id = uuid.uuid4()
    author_id = uuid.uuid4()
    msg = make_chat_message(channel_id=channel_id, author_id=author_id)
    result = MessageOut.model_validate(msg)
    assert result.channel_id == channel_id
    assert result.author_id == author_id

