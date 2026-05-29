from app.schemas.board import BoardOut, ColumnOut, CardOut, CommentOut, ChecklistItemOut, LabelOut
from test.factories import (
    make_board,
    make_board_column,
    make_card,
    make_card_comment,
    make_checklist_item,
    make_card_label,
)
import uuid


def test_board_out_from_model():
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()
    board = make_board(organization_id=org_id, created_by=user_id)
    result = BoardOut.model_validate(board)
    assert result.organization_id == org_id


def test_column_out_from_model():
    board_id = uuid.uuid4()
    column = make_board_column(board_id=board_id)
    result = ColumnOut.model_validate(column)
    assert result.board_id == board_id


def test_card_out_from_model():
    board_id = uuid.uuid4()
    column_id = uuid.uuid4()
    creator_id = uuid.uuid4()
    card = make_card(board_id=board_id, column_id=column_id, creator_id=creator_id)
    result = CardOut.model_validate(card)
    assert result.board_id == board_id


def test_comment_out_from_model():
    card_id = uuid.uuid4()
    author_id = uuid.uuid4()
    comment = make_card_comment(card_id=card_id, author_id=author_id)
    result = CommentOut.model_validate(comment)
    assert result.card_id == card_id


def test_checklist_item_out_from_model():
    card_id = uuid.uuid4()
    item = make_checklist_item(card_id=card_id)
    result = ChecklistItemOut.model_validate(item)
    assert result.card_id == card_id


def test_label_out_from_model():
    board_id = uuid.uuid4()
    label = make_card_label(board_id=board_id)
    result = LabelOut.model_validate(label)
    assert result.board_id == board_id

