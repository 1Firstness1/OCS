import uuid
import pytest
from fastapi import HTTPException
from app.routers.boards import (
    create_board,
    create_column,
    create_card,
    update_card,
    move_card,
    toggle_card_label_on,
    delete_comment,
)
from app.schemas.board import BoardCreate, ColumnCreate, CardCreate, CardUpdate, CardMove
from app.models.member import OrgRole
from test.fakes import FakeAsyncSession, FakeResult
from test.factories import (
    make_board,
    make_board_column,
    make_card,
    make_card_comment,
    make_member,
    make_user,
)


@pytest.mark.asyncio
async def test_create_board_adds_default_columns(mocker):
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[FakeResult(scalar=member)])
    mocker.patch("app.routers.boards.log_action", mocker.AsyncMock())
    data = BoardCreate(name="Board", description=None)
    result = await create_board(org_id=org_id, data=data, current_user=user, db=db)
    assert result.name == "Board"
    assert sum(1 for obj in db.added if obj.__class__.__name__ == "BoardColumn") == 4


@pytest.mark.asyncio
async def test_create_column_uses_next_position(mocker):
    org_id = uuid.uuid4()
    board_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=make_board(org_id, user.id)),
        FakeResult(scalar=2),
    ])
    mocker.patch("app.routers.boards.log_action", mocker.AsyncMock())
    data = ColumnCreate(title="New")
    result = await create_column(org_id=org_id, board_id=board_id, data=data, current_user=user, db=db)
    assert result.position == 3


@pytest.mark.asyncio
async def test_create_card_rejects_missing_column():
    org_id = uuid.uuid4()
    board_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id, role=OrgRole.MODERATOR)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=None),
    ])
    data = CardCreate(title="Card", description=None, priority=make_card(board_id, uuid.uuid4(), user.id).priority, due_date=None, assignee_id=None)
    with pytest.raises(HTTPException) as exc:
        await create_card(org_id=org_id, board_id=board_id, column_id=uuid.uuid4(), data=data, current_user=user, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_card_not_found():
    org_id = uuid.uuid4()
    board_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=None),
    ])
    data = CardUpdate(title="New")
    with pytest.raises(HTTPException) as exc:
        await update_card(org_id=org_id, board_id=board_id, card_id=uuid.uuid4(), data=data, current_user=user, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_move_card_rejects_personal_task_restricted():
    org_id = uuid.uuid4()
    board_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    card = make_card(board_id=board_id, column_id=uuid.uuid4(), creator_id=uuid.uuid4())
    card.assignee_id = uuid.uuid4()
    target_col = make_board_column(board_id=board_id, is_confirmed=False)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=card),
        FakeResult(scalar=target_col),
    ])
    data = CardMove(column_id=target_col.id, position=1)
    with pytest.raises(HTTPException) as exc:
        await move_card(org_id=org_id, board_id=board_id, card_id=card.id, data=data, current_user=user, db=db)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_toggle_card_label_adds_assignment():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=None),
    ])
    result = await toggle_card_label_on(
        org_id=org_id,
        board_id=uuid.uuid4(),
        card_id=uuid.uuid4(),
        label_id=uuid.uuid4(),
        current_user=user,
        db=db,
    )
    assert result == {"status": "added"}
    assert any(obj.__class__.__name__ == "CardLabelAssignment" for obj in db.added)


@pytest.mark.asyncio
async def test_delete_comment_rejects_other_author():
    org_id = uuid.uuid4()
    user = make_user()
    member = make_member(user.id, org_id)
    comment = make_card_comment(card_id=uuid.uuid4(), author_id=uuid.uuid4())
    db = FakeAsyncSession(results=[
        FakeResult(scalar=member),
        FakeResult(scalar=comment),
    ])
    with pytest.raises(HTTPException) as exc:
        await delete_comment(
            org_id=org_id,
            board_id=uuid.uuid4(),
            card_id=uuid.uuid4(),
            comment_id=comment.id,
            current_user=user,
            db=db,
        )
    assert exc.value.status_code == 403

