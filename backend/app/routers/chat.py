import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.chat import ChatChannel, ChatMessage
from app.schemas.chat import ChannelCreate, ChannelOut, MessageCreate, MessageOut
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator

router = APIRouter(prefix="/api/organizations/{org_id}/chat", tags=["chat"])


@router.post("/channels", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
async def create_channel(
    org_id: uuid.UUID,
    data: ChannelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)
    channel = ChatChannel(organization_id=org_id, name=data.name, description=data.description)
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    return ChannelOut.model_validate(channel)


@router.get("/channels", response_model=list[ChannelOut])
async def list_channels(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    result = await db.execute(
        select(ChatChannel).where(ChatChannel.organization_id == org_id)
    )
    return [ChannelOut.model_validate(c) for c in result.scalars().all()]


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    org_id: uuid.UUID,
    channel_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)
    result = await db.execute(
        select(ChatChannel).where(ChatChannel.id == channel_id, ChatChannel.organization_id == org_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=404, detail="not_found")
    await db.delete(channel)
    await db.flush()


@router.post("/channels/{channel_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    org_id: uuid.UUID,
    channel_id: uuid.UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    result = await db.execute(
        select(ChatChannel).where(ChatChannel.id == channel_id, ChatChannel.organization_id == org_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="channel_not_found")

    msg = ChatMessage(channel_id=channel_id, author_id=current_user.id, content=data.content)
    db.add(msg)
    await db.flush()
    await db.refresh(msg)
    return MessageOut(
        id=msg.id, channel_id=msg.channel_id, author_id=msg.author_id,
        content=msg.content, is_deleted=msg.is_deleted, created_at=msg.created_at,
        author_name=current_user.full_name,
    )


@router.get("/channels/{channel_id}/messages", response_model=list[MessageOut])
async def list_messages(
    org_id: uuid.UUID,
    channel_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)
    result = await db.execute(
        select(ChatMessage, User)
        .join(User, User.id == ChatMessage.author_id)
        .where(ChatMessage.channel_id == channel_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = []
    for m, u in result.all():
        messages.append(MessageOut(
            id=m.id, channel_id=m.channel_id, author_id=m.author_id,
            content="[удалено]" if m.is_deleted else m.content,
            is_deleted=m.is_deleted, created_at=m.created_at,
            author_name=u.full_name,
        ))
    return messages


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def moderate_message(
    org_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    actor = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(actor)
    result = await db.execute(select(ChatMessage).where(ChatMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="not_found")
    msg.is_deleted = True
    msg.deleted_by = current_user.id
    await db.flush()
