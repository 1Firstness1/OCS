import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from app.routers.invitations import create_invitation, accept_invitation
from app.schemas.invitation import InvitationCreate
from app.models.invitation import InvitationStatus
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import make_invitation, make_member, make_user


@pytest.mark.asyncio
async def test_create_invitation_rejects_duplicate():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    invite = make_invitation(org_id, user.id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=invite),
    ])
    data = InvitationCreate(email="invitee@example.com")
    with pytest.raises(HTTPException) as exc:
        await create_invitation(org_id=org_id, data=data, current_user=user, db=db)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_create_invitation_success_adds_audit():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=None),
        FakeResult(scalar=None),
        FakeResult(scalar=None),
    ])
    data = InvitationCreate(email="invitee@example.com")
    result = await create_invitation(org_id=org_id, data=data, current_user=user, db=db)
    assert result.organization_id == org_id
    assert len(db.added) >= 2


@pytest.mark.asyncio
async def test_accept_invitation_expired():
    user = make_user(email="invitee@example.com")
    invite = make_invitation(uuid.uuid4(), uuid.uuid4())
    invite.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db = FakeAsyncSession(results=[FakeResult(scalar=invite)])
    with pytest.raises(HTTPException) as exc:
        await accept_invitation(token=invite.token, current_user=user, db=db)
    assert exc.value.status_code == 400
    assert invite.status == InvitationStatus.EXPIRED


@pytest.mark.asyncio
async def test_accept_invitation_success():
    org_id = uuid.uuid4()
    user = make_user(email="invitee@example.com")
    invite = make_invitation(org_id, uuid.uuid4(), email=user.email)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=invite),
        FakeResult(scalar=None),
    ])
    result = await accept_invitation(token=invite.token, current_user=user, db=db)
    assert result == {"detail": "accepted"}
    assert invite.status == InvitationStatus.ACCEPTED
