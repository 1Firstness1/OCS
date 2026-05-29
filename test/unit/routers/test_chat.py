import uuid
import pytest
from fastapi import HTTPException
from app.routers.chat import (
    create_channel,
    list_channels,
    delete_channel,
    send_message,
    list_messages,
    moderate_message,
)
from app.schemas.chat import ChannelCreate, MessageCreate
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_chat_channel, make_chat_message, make_member, make_user


@pytest.mark.asyncio
async def test_create_channel_success():
    org_id = uuid.uuid4()
    user = make_user()
    actor = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[FakeResult(scalar=actor)])
    data = ChannelCreate(name="general", description=None)
    result = await create_channel(org_id=org_id, data=data, current_user=user, db=db)
    assert result.name == "general"


@pytest.mark.asyncio
async def test_list_channels_returns_items():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    channel = make_chat_channel(organization_id=org_id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalars=[channel]),
    ])
    result = await list_channels(org_id=org_id, current_user=user, db=db)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_delete_channel_not_found():
    org_id = uuid.uuid4()
    user = make_user()
    actor = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=actor),
        FakeResult(scalar=None),
    ])
    with pytest.raises(HTTPException) as exc:
        await delete_channel(org_id=org_id, channel_id=uuid.uuid4(), current_user=user, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_send_message_channel_not_found():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=None),
    ])
    data = MessageCreate(content="Hi")
    with pytest.raises(HTTPException) as exc:
        await send_message(org_id=org_id, channel_id=uuid.uuid4(), data=data, current_user=user, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_messages_returns_items():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    msg = make_chat_message(channel_id=uuid.uuid4(), author_id=user.id, content="Hello")
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(all_rows=[(msg, user)]),
    ])
    result = await list_messages(org_id=org_id, channel_id=uuid.uuid4(), current_user=user, db=db)
    assert result[0].content == "Hello"


@pytest.mark.asyncio
async def test_moderate_message_marks_deleted():
    org_id = uuid.uuid4()
    user = make_user()
    actor = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    msg = make_chat_message(channel_id=uuid.uuid4(), author_id=uuid.uuid4())
    db = FakeAsyncSession(results=[
        FakeResult(scalar=actor),
        FakeResult(scalar=msg),
    ])
    await moderate_message(org_id=org_id, message_id=msg.id, current_user=user, db=db)
    assert msg.is_deleted is True
    assert msg.deleted_by == user.id
