import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.models.board import Board, BoardColumn, Card, CardLabel, CardLabelAssignment, CardComment, ChecklistItem
from app.models.notification import Notification
from app.schemas.board import (
    BoardCreate, BoardOut, ColumnCreate, ColumnUpdate, ColumnReorder, ColumnOut,
    CardCreate, CardUpdate, CardMove, CardOut, LabelCreate, LabelOut,
    CommentCreate, CommentOut, ChecklistItemCreate, ChecklistItemUpdate, ChecklistItemOut
)
from app.utils.auth import get_current_user
from app.utils.permissions import get_member_or_fail, require_moderator
from app.utils.audit import log_action

router = APIRouter(prefix="/api/organizations/{org_id}/boards", tags=["boards"])


async def _create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    title: str,
    message: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
):
    db.add(
        Notification(
            user_id=user_id,
            organization_id=org_id,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    )


@router.post("/", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
async def create_board(
    org_id: uuid.UUID,
    data: BoardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(member)

    board = Board(
        organization_id=org_id,
        name=data.name,
        description=data.description,
        created_by=current_user.id,
    )
    db.add(board)
    await db.flush()

    # Create default columns
    default_columns = [
        ("Бэклог", False),
        ("В работе", False),
        ("Готово", False),
        ("Подтверждено", True),
    ]
    for i, (title, is_confirmed) in enumerate(default_columns):
        db.add(BoardColumn(board_id=board.id, title=title, position=i, is_confirmed=is_confirmed))

    await db.flush()
    await db.refresh(board, ["columns", "labels"])
    for col in board.columns:
        set_committed_value(col, "cards", [])
        
    await log_action(
        db, current_user.id, org_id,
        "Создание доски", "Доска", str(board.id),
        f"Создана доска '{board.name}'"
    )
        
    return board


@router.get("/", response_model=List[BoardOut])
async def list_boards(
    org_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(
        select(Board)
        .where(Board.organization_id == org_id)
        .options(
            selectinload(Board.columns),
            selectinload(Board.labels),
        )
        .order_by(Board.created_at.desc())
    )
    boards = result.scalars().all()
    for board in boards:
        for col in board.columns:
            set_committed_value(col, "cards", [])
    return boards


@router.get("/{board_id}", response_model=BoardOut)
async def get_board(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(
        select(Board)
        .where(Board.id == board_id, Board.organization_id == org_id)
        .options(
            selectinload(Board.labels),
            selectinload(Board.columns).selectinload(BoardColumn.cards).selectinload(Card.label_assignments).selectinload(CardLabelAssignment.label),
            selectinload(Board.columns).selectinload(BoardColumn.cards).selectinload(Card.comments).selectinload(CardComment.author),
            selectinload(Board.columns).selectinload(BoardColumn.cards).selectinload(Card.checklist_items),
        )
    )
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="board_not_found")

    # Manually sort columns and cards by position
    board.columns.sort(key=lambda c: c.position)
    for col in board.columns:
        col.cards.sort(key=lambda c: c.position)
        for card in col.cards:
            card.comments.sort(key=lambda c: c.created_at)
            for comment in card.comments:
                comment.author_name = comment.author.full_name if comment.author else None
            card.checklist = sorted(card.checklist_items, key=lambda c: c.position)
            card.labels = [la.label for la in card.label_assignments]

    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(select(Board).where(Board.id == board_id, Board.organization_id == org_id))
    board = result.scalar_one_or_none()
    if not board:
        raise HTTPException(status_code=404, detail="board_not_found")

    if member.role != "moderator" and board.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="not_authorized")

    await db.delete(board)


@router.post("/{board_id}/columns", response_model=ColumnOut)
async def create_column(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    data: ColumnCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(member)

    result = await db.execute(select(Board).where(Board.id == board_id, Board.organization_id == org_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="board_not_found")

    # Get max position
    pos_res = await db.execute(
        select(BoardColumn.position).where(BoardColumn.board_id == board_id).order_by(BoardColumn.position.desc()).limit(1)
    )
    max_pos = pos_res.scalar_one_or_none()
    next_pos = (max_pos + 1) if max_pos is not None else 0

    col = BoardColumn(board_id=board_id, title=data.title, position=next_pos)
    db.add(col)
    await db.flush()
    await db.refresh(col)
    
    await log_action(
        db, current_user.id, org_id,
        "Создание колонки", "Колонка", str(col.id),
        f"Создана колонка '{col.title}' на доске"
    )
    
    return col


@router.put("/{board_id}/columns/{col_id}", response_model=ColumnOut)
async def update_column(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    col_id: uuid.UUID,
    data: ColumnUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(member)

    result = await db.execute(select(BoardColumn).where(BoardColumn.id == col_id, BoardColumn.board_id == board_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="column_not_found")

    if data.title is not None:
        col.title = data.title

    await db.flush()
    return col


@router.delete("/{board_id}/columns/{col_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    col_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(member)

    result = await db.execute(select(BoardColumn).where(BoardColumn.id == col_id, BoardColumn.board_id == board_id))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="column_not_found")

    await db.delete(col)


@router.put("/{board_id}/columns/reorder", status_code=status.HTTP_200_OK)
async def reorder_columns(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    data: List[ColumnReorder],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(member)

    col_ids = [d.column_id for d in data]
    result = await db.execute(select(BoardColumn).where(BoardColumn.id.in_(col_ids), BoardColumn.board_id == board_id))
    cols = {c.id: c for c in result.scalars().all()}

    for d in data:
        if d.column_id in cols:
            cols[d.column_id].position = d.position

    await db.flush()
    return {"status": "ok"}


@router.post("/{board_id}/cards", response_model=CardOut)
async def create_card(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    data: CardCreate,
    column_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)
    require_moderator(member)

    # Check col
    result = await db.execute(select(BoardColumn).where(BoardColumn.id == column_id, BoardColumn.board_id == board_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="column_not_found")

    pos_res = await db.execute(
        select(Card.position).where(Card.column_id == column_id).order_by(Card.position.desc()).limit(1)
    )
    max_pos = pos_res.scalar_one_or_none()
    next_pos = (max_pos + 1) if max_pos is not None else 0

    card = Card(
        board_id=board_id,
        column_id=column_id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        creator_id=current_user.id,
        assignee_id=data.assignee_id,
        position=next_pos,
    )
    db.add(card)
    await db.flush()
    await db.refresh(card)

    set_committed_value(card, "label_assignments", [])
    set_committed_value(card, "comments", [])
    set_committed_value(card, "checklist_items", [])
    card.labels = []
    card.checklist = []

    if card.assignee_id:
        await _create_notification(
            db,
            user_id=card.assignee_id,
            org_id=org_id,
            title="Новая задача",
            message=f"Вам назначена задача: {card.title}",
            entity_type="card",
            entity_id=str(card.id),
        )

    await log_action(
        db, current_user.id, org_id,
        "Создание задачи", "Задача", str(card.id),
        f"Создана задача '{card.title}'"
    )

    return card


@router.put("/{board_id}/cards/{card_id}", response_model=CardOut)
async def update_card(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    data: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(
        select(Card)
        .where(Card.id == card_id, Card.board_id == board_id)
        .options(
            selectinload(Card.label_assignments).selectinload(CardLabelAssignment.label),
            selectinload(Card.comments).selectinload(CardComment.author),
            selectinload(Card.checklist_items)
        )
    )
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="card_not_found")

    prev_assignee = card.assignee_id

    if data.title is not None:
        card.title = data.title
    if data.description is not None:
        card.description = data.description
    if data.priority is not None:
        card.priority = data.priority
    if data.due_date is not None:
        card.due_date = data.due_date
    if data.assignee_id is not None:
        card.assignee_id = data.assignee_id

    await db.flush()

    if data.assignee_id is not None and data.assignee_id != prev_assignee:
        await _create_notification(
            db,
            user_id=data.assignee_id,
            org_id=org_id,
            title="Назначение задачи",
            message=f"Вам назначена задача: {card.title}",
            entity_type="card",
            entity_id=str(card.id),
        )

    card.labels = [la.label for la in card.label_assignments]
    card.comments.sort(key=lambda c: c.created_at)
    for comment in card.comments:
        comment.author_name = comment.author.full_name if comment.author else None
    card.checklist = sorted(card.checklist_items, key=lambda c: c.position)

    await log_action(
        db, current_user.id, org_id,
        "Обновление задачи", "Задача", str(card.id),
        f"Обновлены параметры задачи '{card.title}'"
    )

    return card


@router.put("/{board_id}/cards/{card_id}/move", status_code=status.HTTP_200_OK)
async def move_card(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    data: CardMove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(select(Card).where(Card.id == card_id, Card.board_id == board_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="card_not_found")

    col_result = await db.execute(select(BoardColumn).where(BoardColumn.id == data.column_id, BoardColumn.board_id == board_id))
    target_col = col_result.scalar_one_or_none()
    if not target_col:
        raise HTTPException(status_code=404, detail="column_not_found")

    if target_col.is_confirmed:
        require_moderator(member)
    elif card.assignee_id and card.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="personal_task_restricted")

    # Shift positions in target column
    if card.column_id == data.column_id:
        if card.position < data.position:
            # Moving down
            await db.execute(
                Card.__table__.update()
                .where(Card.column_id == data.column_id, Card.position > card.position, Card.position <= data.position)
                .values(position=Card.position - 1)
            )
        elif card.position > data.position:
            # Moving up
            await db.execute(
                Card.__table__.update()
                .where(Card.column_id == data.column_id, Card.position < card.position, Card.position >= data.position)
                .values(position=Card.position + 1)
            )
    else:
        # Shift down old column
        await db.execute(
            Card.__table__.update()
            .where(Card.column_id == card.column_id, Card.position > card.position)
            .values(position=Card.position - 1)
        )
        # Shift up new column
        await db.execute(
            Card.__table__.update()
            .where(Card.column_id == data.column_id, Card.position >= data.position)
            .values(position=Card.position + 1)
        )

    card.column_id = data.column_id
    card.position = data.position
    await db.flush()

    if target_col.is_confirmed:
        notify_ids = {card.creator_id}
        if card.assignee_id:
            notify_ids.add(card.assignee_id)
        notify_ids.discard(current_user.id)
        for user_id in notify_ids:
            await _create_notification(
                db,
                user_id=user_id,
                org_id=org_id,
                title="Задача подтверждена",
                message=f"Задача подтверждена модератором: {card.title}",
                entity_type="card",
                entity_id=str(card.id),
            )

    await log_action(
        db, current_user.id, org_id,
        "Перемещение задачи", "Задача", str(card.id),
        f"Задача '{card.title}' перемещена в колонку {target_col.title}"
    )

    return {"status": "ok"}


@router.delete("/{board_id}/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(select(Card).where(Card.id == card_id, Card.board_id == board_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="card_not_found")

    await log_action(
        db, current_user.id, org_id,
        "Удаление задачи", "Задача", str(card.id),
        f"Удалена задача '{card.title}'"
    )

    await db.delete(card)


@router.post("/{board_id}/labels", response_model=LabelOut)
async def create_label(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    data: LabelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    lbl = CardLabel(board_id=board_id, name=data.name, color=data.color)
    db.add(lbl)
    await db.flush()
    await db.refresh(lbl)
    return lbl


@router.delete("/{board_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(select(CardLabel).where(CardLabel.id == label_id, CardLabel.board_id == board_id))
    lbl = result.scalar_one_or_none()
    if not lbl:
        raise HTTPException(status_code=404, detail="label_not_found")

    await db.delete(lbl)


@router.post("/{board_id}/cards/{card_id}/labels/{label_id}", status_code=status.HTTP_200_OK)
async def toggle_card_label_on(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    existing = await db.execute(select(CardLabelAssignment).where(CardLabelAssignment.card_id == card_id, CardLabelAssignment.label_id == label_id))
    if not existing.scalar_one_or_none():
        assignment = CardLabelAssignment(card_id=card_id, label_id=label_id)
        db.add(assignment)
        await db.flush()

    return {"status": "added"}


@router.delete("/{board_id}/cards/{card_id}/labels/{label_id}", status_code=status.HTTP_200_OK)
async def toggle_card_label_off(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    existing = await db.execute(select(CardLabelAssignment).where(CardLabelAssignment.card_id == card_id, CardLabelAssignment.label_id == label_id))
    assign = existing.scalar_one_or_none()
    if assign:
        await db.delete(assign)
        await db.flush()

    return {"status": "removed"}


@router.post("/{board_id}/cards/{card_id}/comments", response_model=CommentOut)
async def add_comment(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    comment = CardComment(
        card_id=card_id,
        author_id=current_user.id,
        content=data.content
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment, ["author"])

    card_result = await db.execute(
        select(Card).where(Card.id == card_id, Card.board_id == board_id)
    )
    card = card_result.scalar_one_or_none()
    if card:
        notify_ids = {card.creator_id}
        if card.assignee_id:
            notify_ids.add(card.assignee_id)
        notify_ids.discard(current_user.id)
        for user_id in notify_ids:
            await _create_notification(
                db,
                user_id=user_id,
                org_id=org_id,
                title="Новый комментарий",
                message=f"Комментарий к задаче: {card.title}",
                entity_type="card",
                entity_id=str(card.id),
            )

    await log_action(
        db, current_user.id, org_id,
        "Новый комментарий", "Комментарий", str(comment.id),
        f"Новый комментарий к задаче '{card.title}'" if card else "Новый комментарий"
    )

    out = CommentOut.model_validate(comment)
    out.author_name = comment.author.full_name
    return out


@router.delete("/{board_id}/cards/{card_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    comment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(select(CardComment).where(CardComment.id == comment_id, CardComment.card_id == card_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="comment_not_found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="not_authorized")

    await db.delete(comment)


@router.post("/{board_id}/cards/{card_id}/checklist", response_model=ChecklistItemOut)
async def add_checklist_item(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    data: ChecklistItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    pos_res = await db.execute(
        select(ChecklistItem.position).where(ChecklistItem.card_id == card_id).order_by(ChecklistItem.position.desc()).limit(1)
    )
    max_pos = pos_res.scalar_one_or_none()
    next_pos = (max_pos + 1) if max_pos is not None else 0

    item = ChecklistItem(
        card_id=card_id,
        text=data.text,
        is_completed=data.is_completed,
        position=next_pos
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/{board_id}/cards/{card_id}/checklist/{item_id}", response_model=ChecklistItemOut)
async def update_checklist_item(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    item_id: uuid.UUID,
    data: ChecklistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(select(ChecklistItem).where(ChecklistItem.id == item_id, ChecklistItem.card_id == card_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="item_not_found")

    if data.text is not None:
        item.text = data.text
    if data.is_completed is not None:
        item.is_completed = data.is_completed
    if data.position is not None:
        item.position = data.position

    await db.flush()
    return item


@router.delete("/{board_id}/cards/{card_id}/checklist/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checklist_item(
    org_id: uuid.UUID,
    board_id: uuid.UUID,
    card_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_member_or_fail(db, current_user.id, org_id)

    result = await db.execute(select(ChecklistItem).where(ChecklistItem.id == item_id, ChecklistItem.card_id == card_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="item_not_found")

    await db.delete(item)
