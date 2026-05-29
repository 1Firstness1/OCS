import { useState, useEffect, useRef } from 'react';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

function getInitials(name) {
  return name ? name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) : '?';
}

function PriorityIcon({ priority }) {
  const pMap = {
    low: { char: 'L', class: 'priority-low' },
    medium: { char: 'M', class: 'priority-medium' },
    high: { char: 'H', class: 'priority-high' },
    urgent: { char: 'U', class: 'priority-urgent' }
  };
  const info = pMap[priority] || pMap.medium;
  return <span className={`priority-icon ${info.class}`}>{info.char}</span>;
}

export default function KanbanBoard({ orgId, members, isModerator }) {
  const { user } = useAuth();
  const [boards, setBoards] = useState([]);
  const [selectedBoardId, setSelectedBoardId] = useState('');
  const [board, setBoard] = useState(null);
  
  const [loading, setLoading] = useState(true);
  const [showCreateBoard, setShowCreateBoard] = useState(false);
  const [newBoardName, setNewBoardName] = useState('');
  const [newBoardDesc, setNewBoardDesc] = useState('');

  // Drag and drop state
  const [draggedCard, setDraggedCard] = useState(null);
  const [draggedOverCol, setDraggedOverCol] = useState(null);

  // Modals
  const [editingCard, setEditingCard] = useState(null);
  const [showAddCol, setShowAddCol] = useState(false);
  const [addingCardToCol, setAddingCardToCol] = useState(null);
  const [newCardTitle, setNewCardTitle] = useState('');
  const [newComment, setNewComment] = useState('');
  const [newChecklistText, setNewChecklistText] = useState('');

  const canEditCardDetails = isModerator;
  const isAssigneeOrUnassigned = !editingCard?.assignee_id || editingCard?.assignee_id === user.id;
  const canInteract = isModerator || isAssigneeOrUnassigned;

  useEffect(() => {
    loadBoards();
  }, [orgId]);

  useEffect(() => {
    if (selectedBoardId) {
      loadBoardDetails(selectedBoardId);
    } else {
      setBoard(null);
    }
  }, [selectedBoardId]);

  const loadBoards = async () => {
    try {
      const data = await api.getBoards(orgId);
      setBoards(data);
      if (data.length > 0 && !selectedBoardId) {
        setSelectedBoardId(data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadBoardDetails = async (bId) => {
    try {
      const b = await api.getBoard(orgId, bId);
      setBoard(b);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateBoard = async (e) => {
    e.preventDefault();
    try {
      const b = await api.createBoard(orgId, { name: newBoardName, description: newBoardDesc });
      setBoards([b, ...boards]);
      setSelectedBoardId(b.id);
      setShowCreateBoard(false);
      setNewBoardName('');
      setNewBoardDesc('');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteBoard = async () => {
    if (!confirm('Удалить доску и все её задачи?')) return;
    try {
      await api.deleteBoard(orgId, selectedBoardId);
      const remaining = boards.filter(b => b.id !== selectedBoardId);
      setBoards(remaining);
      setSelectedBoardId(remaining.length > 0 ? remaining[0].id : '');
    } catch (err) {
      alert(err.message);
    }
  };


  const handleCreateCard = async (e, colId) => {
    e.preventDefault();
    try {
      const card = await api.createCard(orgId, board.id, colId, { title: newCardTitle, priority: 'medium' });
      setBoard(prev => ({
        ...prev,
        columns: prev.columns.map(c => c.id === colId ? { ...c, cards: [...c.cards, card] } : c)
      }));
      setAddingCardToCol(null);
      setNewCardTitle('');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteCard = async (cardId, colId) => {
    if(!confirm('Удалить карточку?')) return;
    try {
      await api.deleteCard(orgId, board.id, cardId);
      setBoard(prev => ({
        ...prev,
        columns: prev.columns.map(c => c.id === colId ? { ...c, cards: c.cards.filter(card => card.id !== cardId) } : c)
      }));
      setEditingCard(null);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleUpdateCard = async (updates) => {
    try {
      const updated = await api.updateCard(orgId, board.id, editingCard.id, updates);
      setEditingCard(updated);
      // Update in board state
      setBoard(prev => ({
        ...prev,
        columns: prev.columns.map(c => 
          c.id === updated.column_id 
          ? { ...c, cards: c.cards.map(card => card.id === updated.id ? updated : card) }
          : c
        )
      }));
    } catch (err) {
      alert(err.message);
    }
  };

  // Drag and Drop
  const onDragStart = (e, card, colId) => {
    setDraggedCard({ ...card, sourceColId: colId });
    e.dataTransfer.effectAllowed = 'move';
    // Small delay to allow dragging class to apply
    setTimeout(() => {
      e.target.classList.add('dragging');
    }, 0);
  };

  const onDragEnd = (e) => {
    e.target.classList.remove('dragging');
    setDraggedCard(null);
    setDraggedOverCol(null);
  };

  const onDragOver = (e, colId) => {
    e.preventDefault();
    if (draggedOverCol !== colId) {
      setDraggedOverCol(colId);
    }
  };

  const onDrop = async (e, targetColId) => {
    e.preventDefault();
    if (!draggedCard) return;

    setDraggedOverCol(null);
    const sourceColId = draggedCard.sourceColId;

    // If dropped in the same column, ideally we'd reorder, but for now we just skip or append to end
    // To properly support reorder inside column, we'd need drop targets between cards
    // For simplicity: just moving between columns or to the end of same column
    if (sourceColId === targetColId) return;

    const targetCol = board.columns.find(c => c.id === targetColId);
    if (!targetCol) return;
    if (targetCol.is_confirmed && !isModerator) {
      alert('Подтверждение задачи доступно только модератору');
      return;
    }

    try {
      // Optimistic update
      const newPos = targetCol.cards.length; // Append to end
      
      setBoard(prev => {
        const newCols = prev.columns.map(c => {
          if (c.id === sourceColId) {
            return { ...c, cards: c.cards.filter(card => card.id !== draggedCard.id) };
          }
          if (c.id === targetColId) {
            return { ...c, cards: [...c.cards, { ...draggedCard, column_id: targetColId, position: newPos }] };
          }
          return c;
        });
        return { ...prev, columns: newCols };
      });

      await api.moveCard(orgId, board.id, draggedCard.id, { column_id: targetColId, position: newPos });
    } catch (err) {
      alert('Ошибка при перемещении: ' + err.message);
      loadBoardDetails(board.id); // Revert
    }
  };

  // Comments
  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    try {
      const comment = await api.addCardComment(orgId, board.id, editingCard.id, { content: newComment });
      setEditingCard(prev => ({ ...prev, comments: [...prev.comments, comment] }));
      setNewComment('');
    } catch(err) {
      alert(err.message);
    }
  };
  
  const handleDeleteComment = async (commentId) => {
    try {
      await api.deleteCardComment(orgId, board.id, editingCard.id, commentId);
      setEditingCard(prev => ({ ...prev, comments: prev.comments.filter(c => c.id !== commentId) }));
    } catch(err) {
      alert(err.message);
    }
  };

  // Checklist
  const handleAddChecklist = async (e) => {
    e.preventDefault();
    if(!newChecklistText.trim()) return;
    try {
      const item = await api.addChecklistItem(orgId, board.id, editingCard.id, { text: newChecklistText, is_completed: false });
      setEditingCard(prev => ({ ...prev, checklist: [...prev.checklist, item] }));
      setNewChecklistText('');
    } catch(err) {
      alert('Ошибка: только модератор может добавлять чеклисты');
    }
  };

  const handleToggleChecklist = async (item) => {
    try {
      const updated = await api.updateChecklistItem(orgId, board.id, editingCard.id, item.id, { is_completed: !item.is_completed });
      setEditingCard(prev => ({ 
        ...prev, 
        checklist: prev.checklist.map(c => c.id === item.id ? updated : c) 
      }));
    } catch(err) {
      alert(err.message);
    }
  };

  const handleDeleteChecklist = async (itemId) => {
    try {
      await api.deleteChecklistItem(orgId, board.id, editingCard.id, itemId);
      setEditingCard(prev => ({ 
        ...prev, 
        checklist: prev.checklist.filter(c => c.id !== itemId) 
      }));
    } catch(err) {
      alert(err.message);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <div className="kanban-container">
      <div className="kanban-header">
        <div className="kanban-boards-select">
          <select 
            className="form-select" 
            style={{ width: '250px' }}
            value={selectedBoardId} 
            onChange={e => setSelectedBoardId(e.target.value)}
          >
            {boards.length === 0 && <option value="">Нет доступных досок</option>}
            {boards.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          {isModerator && (
            <button className="btn btn-secondary btn-sm" onClick={() => setShowCreateBoard(true)}>
              + Новая доска
            </button>
          )}
        </div>
        {board && isModerator && (
          <button className="btn btn-link btn-sm" style={{ color: 'var(--text-muted)' }} onClick={handleDeleteBoard}>
            Удалить доску
          </button>
        )}
      </div>

      {board ? (
        <div className="kanban-board">
          {board.columns.map(col => (
            <div 
              key={col.id} 
              className="kanban-column"
              onDragOver={(e) => onDragOver(e, col.id)}
              onDrop={(e) => onDrop(e, col.id)}
              style={{ border: draggedOverCol === col.id ? '1px dashed var(--accent)' : '' }}
            >
              <div className="kanban-column-header">
                <span>{col.title}</span>
                <span className="kanban-column-count">{col.cards.length}</span>
              </div>
              <div className="kanban-column-cards">
                {col.cards.map(card => (
                  <div 
                    key={card.id} 
                    className="kanban-card"
                    draggable
                    onDragStart={(e) => onDragStart(e, card, col.id)}
                    onDragEnd={onDragEnd}
                    onClick={() => setEditingCard(card)}
                  >
                    {card.labels && card.labels.length > 0 && (
                      <div className="kanban-card-badges">
                        {card.labels.map(l => (
                          <div key={l.id} className="kanban-label-sm" style={{ backgroundColor: l.color }} title={l.name}></div>
                        ))}
                      </div>
                    )}
                    <div className="kanban-card-title">{card.title}</div>
                    <div className="kanban-card-meta">
                      <PriorityIcon priority={card.priority} />
                      {card.assignee_id && (
                        <div className="comment-avatar" style={{ width: 20, height: 20, fontSize: 9 }}>
                          {getInitials(members.find(m => m.user_id === card.assignee_id)?.full_name)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {addingCardToCol === col.id ? (
                  <form onSubmit={(e) => handleCreateCard(e, col.id)}>
                    <input 
                      autoFocus
                      className="form-input" 
                      style={{ marginBottom: 8 }}
                      placeholder="Название задачи..." 
                      value={newCardTitle} 
                      onChange={e => setNewCardTitle(e.target.value)} 
                      required 
                    />
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button type="submit" className="btn btn-primary btn-sm">Создать</button>
                      <button type="button" className="btn btn-secondary btn-sm" onClick={() => setAddingCardToCol(null)}>Отмена</button>
                    </div>
                  </form>
                ) : (
                  <div className="kanban-column-add">
                    {isModerator && (
                      <button onClick={() => setAddingCardToCol(col.id)}>+ Добавить карточку</button>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Column creation removed as requested */}
        </div>
      ) : (
        <div className="empty-state">
          <p>Выберите доску или создайте новую</p>
        </div>
      )}

      {/* CREATE BOARD MODAL */}
      {showCreateBoard && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowCreateBoard(false)}>
          <div className="modal">
            <h2>Создать Kanban-доску</h2>
            <form onSubmit={handleCreateBoard}>
              <div className="form-group">
                <label>Название доски</label>
                <input className="form-input" value={newBoardName} onChange={e => setNewBoardName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea className="form-textarea" value={newBoardDesc} onChange={e => setNewBoardDesc(e.target.value)} />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateBoard(false)}>Отмена</button>
                <button type="submit" className="btn btn-primary">Создать</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CARD EDIT MODAL */}
      {editingCard && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setEditingCard(null)}>
          <div className="card-modal modal">
            <div className="card-modal-header">
              <h2 style={{ margin: 0 }}>{editingCard.title}</h2>
              <button className="btn btn-link" style={{ color: 'var(--text-muted)' }} onClick={() => setEditingCard(null)}>✕</button>
            </div>
            <div className="card-modal-body">
              <div className="card-modal-main">
                <div className="form-group">
                  <label>Описание задачи</label>
                  <textarea 
                    className="form-textarea" 
                    value={editingCard.description || ''} 
                    onChange={e => setEditingCard({...editingCard, description: e.target.value})}
                    onBlur={() => canEditCardDetails && handleUpdateCard({ description: editingCard.description })}
                    placeholder="Добавьте более подробное описание..."
                    style={{ minHeight: 120 }}
                    disabled={!canEditCardDetails}
                  />
                </div>

                <div className="form-group" style={{ marginTop: 24 }}>
                  <label>Чеклист</label>
                  <div style={{ marginBottom: 12 }}>
                    {editingCard.checklist.map(item => (
                      <div key={item.id} className={`checklist-item ${item.is_completed ? 'completed' : ''}`}>
                        <input 
                          type="checkbox" 
                          checked={item.is_completed} 
                          onChange={() => canInteract && handleToggleChecklist(item)} 
                          disabled={!canInteract}
                        />
                        <div className="checklist-item-text">{item.text}</div>
                        {canEditCardDetails && (
                          <button className="btn btn-link btn-sm" style={{ color: 'var(--danger)', padding: 0 }} onClick={() => handleDeleteChecklist(item.id)}>Удалить</button>
                        )}
                      </div>
                    ))}
                  </div>
                  {canEditCardDetails && (
                    <form onSubmit={handleAddChecklist} style={{ display: 'flex', gap: 8 }}>
                      <input className="form-input" placeholder="Добавить элемент..." value={newChecklistText} onChange={e => setNewChecklistText(e.target.value)} />
                      <button type="submit" className="btn btn-secondary">Добавить</button>
                    </form>
                  )}
                </div>

                <div className="form-group" style={{ marginTop: 32 }}>
                  <label>Комментарии</label>
                  <div style={{ marginBottom: 16 }}>
                    {editingCard.comments.map(c => (
                      <div key={c.id} className="comment-item">
                        <div className="comment-avatar">
                          {getInitials(c.author_name)}
                        </div>
                        <div className="comment-content">
                          <div className="comment-header">
                            <span className="comment-author">{c.author_name}</span>
                            <div style={{ display: 'flex', gap: 10 }}>
                              <span className="comment-time">{new Date(c.created_at).toLocaleString('ru-RU')}</span>
                              {c.author_id === user.id && (
                                <button className="btn btn-link" style={{ fontSize: 11, padding: 0, color: 'var(--danger)' }} onClick={() => handleDeleteComment(c.id)}>Удал.</button>
                              )}
                            </div>
                          </div>
                          <div className="comment-text">{c.content}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {canInteract ? (
                    <form onSubmit={handleAddComment}>
                      <textarea 
                        className="form-textarea" 
                        style={{ minHeight: 60, marginBottom: 8 }} 
                        placeholder="Написать комментарий..."
                        value={newComment}
                        onChange={e => setNewComment(e.target.value)}
                      />
                      <button type="submit" className="btn btn-primary">Отправить</button>
                    </form>
                  ) : (
                    <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Вы не можете комментировать эту задачу</div>
                  )}
                </div>
              </div>

              <div className="card-modal-sidebar">
                <div className="form-group">
                  <label>Исполнитель</label>
                  <select 
                    className="form-select" 
                    value={editingCard.assignee_id || ''} 
                    onChange={e => handleUpdateCard({ assignee_id: e.target.value || null })}
                    disabled={!canEditCardDetails}
                  >
                    <option value="">Не назначен</option>
                    {members.map(m => (
                      <option key={m.user_id} value={m.user_id}>{m.full_name}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Приоритет</label>
                  <select 
                    className="form-select" 
                    value={editingCard.priority} 
                    onChange={e => handleUpdateCard({ priority: e.target.value })}
                    disabled={!canEditCardDetails}
                  >
                    <option value="low">Низкий (Low)</option>
                    <option value="medium">Средний (Medium)</option>
                    <option value="high">Высокий (High)</option>
                    <option value="urgent">Срочно (Urgent)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Дедлайн</label>
                  <input 
                    type="date" 
                    className="form-input" 
                    value={editingCard.due_date || ''} 
                    onChange={e => handleUpdateCard({ due_date: e.target.value || null })}
                    disabled={!canEditCardDetails}
                  />
                </div>

                {canEditCardDetails && (
                  <div style={{ marginTop: 32 }}>
                    <button className="btn btn-danger" style={{ width: '100%' }} onClick={() => handleDeleteCard(editingCard.id, editingCard.column_id)}>
                      Удалить карточку
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}