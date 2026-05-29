import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';
import KanbanBoard from '../components/KanbanBoard';

const TABS = [
  { id: 'overview', label: 'Обзор' },
  { id: 'members', label: 'Участники' },
  { id: 'departments', label: 'Отделы' },
  { id: 'chat', label: 'Чат' },
  { id: 'tasks', label: 'Задачи' },
  { id: 'finance', label: 'Финансы' },
  { id: 'absences', label: 'Отсутствия' },
  { id: 'logs', label: 'Логи' }
];

const ORG_CATEGORIES = [
  { value: 'it', label: 'IT' },
  { value: 'marketing', label: 'Маркетинг' },
  { value: 'hr', label: 'HR' },
  { value: 'finance', label: 'Финансы' },
  { value: 'sales', label: 'Продажи' },
  { value: 'education', label: 'Образование' },
  { value: 'healthcare', label: 'Здравоохранение' },
  { value: 'nonprofit', label: 'НКО' },
  { value: 'other', label: 'Другое' }
];

export default function OrganizationPage() {
  const { orgId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [org, setOrg] = useState(null);
  const [members, setMembers] = useState([]);
  const [currentMember, setCurrentMember] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('members');
  const [error, setError] = useState('');

  // Members & Invite states
  const [inviteEmail, setInviteEmail] = useState('');
  const [invites, setInvites] = useState([]);
  const [showMemberModal, setShowMemberModal] = useState(null); // stores member object
  const [selectedRole, setSelectedRole] = useState('employee');
  const [selectedPosition, setSelectedPosition] = useState('');
  const [selectedDept, setSelectedDept] = useState('');

  // Departments states
  const [depts, setDepts] = useState([]);
  const [newDeptName, setNewDeptName] = useState('');
  const [newDeptDesc, setNewDeptDesc] = useState('');
  const [viewingDept, setViewingDept] = useState(null);
  const [deptMembers, setDeptMembers] = useState([]);

  // Logs state
  const [orgLogs, setOrgLogs] = useState([]);
  const [logsSearch, setLogsSearch] = useState('');

  // Chat states
  const [channels, setChannels] = useState([]);
  const [activeChannel, setActiveChannel] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [newChannelName, setNewChannelName] = useState('');
  const [newChannelDesc, setNewChannelDesc] = useState('');
  const [showNewChannelModal, setShowNewChannelModal] = useState(false);
  const messagesEndRef = useRef(null);

  // Finance states
  const [finance, setFinance] = useState([]);
  const [newFinTitle, setNewFinTitle] = useState('');
  const [newFinDesc, setNewFinDesc] = useState('');
  const [newFinAmount, setNewFinAmount] = useState('');
  const [newFinCat, setNewFinCat] = useState('expense');

  // Absence states
  const [absences, setAbsences] = useState([]);
  const [newAbsType, setNewAbsType] = useState('vacation');
  const [newAbsStart, setNewAbsStart] = useState('');
  const [newAbsEnd, setNewAbsEnd] = useState('');
  const [newAbsReason, setNewAbsReason] = useState('');

  // Settings states
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editCategory, setEditCategory] = useState('other');
  const [editWebsite, setEditWebsite] = useState('');
  const [editPhone, setEditPhone] = useState('');
  const [editAddress, setEditAddress] = useState('');
  const [editSize, setEditSize] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([
      api.getOrganization(orgId),
      api.getMembers(orgId),
      api.getDepartments(orgId),
    ])
      .then(([orgData, membersData, deptsData]) => {
        setOrg(orgData);
        setEditName(orgData.name);
        setEditDesc(orgData.description || '');
        setEditCategory(orgData.category || 'other');
        setEditWebsite(orgData.data?.website || '');
        setEditPhone(orgData.data?.phone || '');
        setEditAddress(orgData.data?.address || '');
        setEditSize(orgData.data?.size || '');
        setMembers(membersData);
        setDepts(deptsData);

        const found = membersData.find(m => m.user_id === user.id);
        setCurrentMember(found || null);
      })
      .catch(err => {
        setError('Не удалось загрузить данные организации: ' + err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [orgId, user.id]);

  // Load contextual tab data
  useEffect(() => {
    if (!org) return;
    if (activeTab === 'members' && currentMember?.role === 'moderator') {
      api.getInvitations(orgId).then(setInvites).catch(() => {});
    } else if (activeTab === 'chat') {
      api.getChannels(orgId)
        .then(chanData => {
          setChannels(chanData);
          if (chanData.length > 0 && !activeChannel) {
            setActiveChannel(chanData[0]);
          }
        })
        .catch(() => {});
    } else if (activeTab === 'finance') {
      api.getFinanceRecords(orgId).then(setFinance).catch(() => {});
    } else if (activeTab === 'absences') {
      api.getAbsences(orgId).then(setAbsences).catch(() => {});
    } else if (activeTab === 'logs') {
      api.getOrganizationLogs(orgId, logsSearch).then(setOrgLogs).catch(() => {});
    }
  }, [activeTab, orgId, org, currentMember, logsSearch]);

  // Load chat messages when active channel changes
  useEffect(() => {
    if (activeTab === 'chat' && activeChannel) {
      api.getMessages(orgId, activeChannel.id)
        .then(setMessages)
        .catch(() => {});
    }
  }, [activeChannel, activeTab, orgId]);

  // Auto-scroll chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  if (loading) return <div className="loading"><div className="spinner" /></div>;
  if (error) return <div className="page-body"><div className="alert alert-error">{error}</div></div>;
  if (!org) return <div className="page-body"><div className="alert alert-error">Организация не найдена</div></div>;

  const isModerator = currentMember?.role === 'moderator' || org.owner_id === user.id;

  // Handlers: Members
  const handleInvite = async (e) => {
    e.preventDefault();
    try {
      const invite = await api.createInvitation(orgId, { email: inviteEmail });
      setInvites(prev => [invite, ...prev]);
      setInviteEmail('');
    } catch (err) {
      alert('Ошибка приглашения: ' + err.message);
    }
  };

  const handleCancelInvite = async (inviteId) => {
    try {
      await api.cancelInvitation(orgId, inviteId);
      setInvites(prev => prev.map(i => i.id === inviteId ? { ...i, status: 'expired' } : i));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleOpenMemberModal = (m) => {
    setShowMemberModal(m);
    setSelectedRole(m.role);
    setSelectedPosition(m.position || '');
    setSelectedDept(m.department_id || '');
  };

  const handleUpdateMember = async (e) => {
    e.preventDefault();
    try {
      const updated = await api.updateMember(orgId, showMemberModal.id, {
        role: selectedRole,
        position: selectedPosition,
        department_id: selectedDept || null
      });
      setMembers(prev => prev.map(m => m.id === updated.id ? { ...m, ...updated } : m));
      setShowMemberModal(null);
    } catch (err) {
      alert('Ошибка сохранения: ' + err.message);
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!confirm('Вы уверены, что хотите удалить этого участника?')) return;
    try {
      await api.removeMember(orgId, memberId);
      setMembers(prev => prev.filter(m => m.id !== memberId));
      setShowMemberModal(null);
    } catch (err) {
      alert(err.message);
    }
  };

  // Handlers: Departments
  const handleCreateDept = async (e) => {
    e.preventDefault();
    try {
      const dept = await api.createDepartment(orgId, { name: newDeptName, description: newDeptDesc });
      setDepts(prev => [...prev, dept]);
      setNewDeptName('');
      setNewDeptDesc('');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteDept = async (deptId) => {
    if (!confirm('Удалить отдел? Участники этого отдела будут переведены в общий список.')) return;
    try {
      await api.deleteDepartment(orgId, deptId);
      setDepts(prev => prev.filter(d => d.id !== deptId));
      // Refresh members since department associations updated
      api.getMembers(orgId).then(setMembers).catch(() => {});
    } catch (err) {
      alert(err.message);
    }
  };

  const handleViewDept = async (dept) => {
    try {
      const members = await api.getDepartmentMembers(orgId, dept.id);
      setDeptMembers(members);
      setViewingDept(dept);
    } catch (err) {
      alert(err.message);
    }
  };

  // Handlers: Chat
  const handleCreateChannel = async (e) => {
    e.preventDefault();
    try {
      const chan = await api.createChannel(orgId, { name: newChannelName, description: newChannelDesc });
      setChannels(prev => [...prev, chan]);
      setActiveChannel(chan);
      setShowNewChannelModal(false);
      setNewChannelName('');
      setNewChannelDesc('');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteChannel = async (chanId) => {
    if (!confirm('Вы уверены, что хотите удалить этот канал со всей историей сообщений?')) return;
    try {
      await api.deleteChannel(orgId, chanId);
      const remaining = channels.filter(c => c.id !== chanId);
      setChannels(remaining);
      setActiveChannel(remaining.length > 0 ? remaining[0] : null);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeChannel) return;
    try {
      const msg = await api.sendMessage(orgId, activeChannel.id, { content: newMessage });
      setMessages(prev => [...prev, msg]);
      setNewMessage('');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteMessage = async (msgId) => {
    try {
      await api.deleteMessage(orgId, msgId);
      setMessages(prev => prev.map(m => m.id === msgId ? { ...m, is_deleted: true, content: '[удалено]' } : m));
    } catch (err) {
      alert(err.message);
    }
  };

  // Handlers: Finance
  const handleCreateFinance = async (e) => {
    e.preventDefault();
    try {
      const rec = await api.createFinanceRecord(orgId, {
        title: newFinTitle,
        description: newFinDesc || null,
        amount: parseFloat(newFinAmount),
        category: newFinCat
      });
      setFinance(prev => [rec, ...prev]);
      setNewFinTitle('');
      setNewFinDesc('');
      setNewFinAmount('');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleApproveFinance = async (recId, approveStatus) => {
    try {
      const updated = await api.approveFinanceRecord(orgId, recId, { status: approveStatus });
      setFinance(prev => prev.map(f => f.id === recId ? { ...f, ...updated } : f));
    } catch (err) {
      alert(err.message);
    }
  };

  // Handlers: Absences
  const handleCreateAbsence = async (e) => {
    e.preventDefault();
    try {
      const abs = await api.createAbsence(orgId, {
        absence_type: newAbsType,
        start_date: newAbsStart,
        end_date: newAbsEnd,
        reason: newAbsReason || null
      });
      setAbsences(prev => [abs, ...prev]);
      setNewAbsStart('');
      setNewAbsEnd('');
      setNewAbsReason('');
    } catch (err) {
      alert('Ошибка при подаче заявки: ' + err.message);
    }
  };

  const handleApproveAbsence = async (absId, approveStatus) => {
    try {
      const updated = await api.approveAbsence(orgId, absId, { status: approveStatus });
      setAbsences(prev => prev.map(a => a.id === absId ? { ...a, ...updated } : a));
    } catch (err) {
      alert(err.message);
    }
  };

  // Handlers: Settings
  const handleUpdateOrg = async (e) => {
    e.preventDefault();
    try {
      const updated = await api.updateOrganization(orgId, {
        name: editName,
        description: editDesc,
        category: editCategory,
        data: {
          website: editWebsite || null,
          phone: editPhone || null,
          address: editAddress || null,
          size: editSize || null,
        }
      });
      setOrg(updated);
      alert('Изменения сохранены');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteOrg = async () => {
    if (!confirm('ВНИМАНИЕ! Вы действительно хотите безвозвратно удалить эту организацию? Все её данные будут потеряны.')) return;
    try {
      await api.deleteOrganization(orgId);
      navigate('/');
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <>
      <div className="page-header">
        <div className="org-header">
          <div className="org-icon">{org.name[0].toUpperCase()}</div>
          <div>
            <h1>{org.name}</h1>
            <p>{org.description || 'Нет описания организации'}</p>
          </div>
        </div>

        <div className="tabs">
          <button className={`tab${activeTab === 'members' ? ' active' : ''}`} onClick={() => setActiveTab('members')}>Участники</button>
          <button className={`tab${activeTab === 'departments' ? ' active' : ''}`} onClick={() => setActiveTab('departments')}>Отделы</button>
          <button className={`tab${activeTab === 'chat' ? ' active' : ''}`} onClick={() => setActiveTab('chat')}>Чат</button>
          <button className={`tab${activeTab === 'tasks' ? ' active' : ''}`} onClick={() => setActiveTab('tasks')}>Задачи</button>
          <button className={`tab${activeTab === 'finance' ? ' active' : ''}`} onClick={() => setActiveTab('finance')}>Финансы</button>
          <button className={`tab${activeTab === 'absences' ? ' active' : ''}`} onClick={() => setActiveTab('absences')}>Календарь отсутствий</button>
          <button className={`tab${activeTab === 'logs' ? ' active' : ''}`} onClick={() => setActiveTab('logs')}>Логи</button>
          <button className={`tab${activeTab === 'settings' ? ' active' : ''}`} onClick={() => setActiveTab('settings')}>Настройки</button>
        </div>
      </div>

      <div className="page-body">
        {/* MEMBERS TAB */}
        {activeTab === 'members' && (
          <div style={{ display: 'grid', gridTemplateColumns: isModerator ? '2fr 1fr' : '1fr', gap: '24px' }}>
            <div>
              <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Список сотрудников</h2>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Имя</th>
                      <th>Email</th>
                      <th>Отдел</th>
                      <th>Должность</th>
                      <th>Роль</th>
                      {isModerator && <th style={{ width: '40px' }}></th>}
                    </tr>
                  </thead>
                  <tbody>
                    {members.map(m => (
                      <tr key={m.id}>
                        <td style={{ fontWeight: '500' }}>{m.full_name}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{m.email}</td>
                        <td>{depts.find(d => d.id === m.department_id)?.name || <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                        <td>{m.position || <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                        <td>
                          <span className={`badge ${m.role === 'moderator' ? 'badge-info' : 'badge-neutral'}`}>
                            {m.role === 'moderator' ? 'Модератор' : 'Сотрудник'}
                          </span>
                        </td>
                        {isModerator && (
                          <td>
                            <button className="btn btn-secondary btn-sm" onClick={() => handleOpenMemberModal(m)}>Изменить</button>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {isModerator && (
              <div>
                <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Контроль приглашений</h2>
                <form onSubmit={handleInvite} className="card" style={{ marginBottom: '20px' }}>
                  <div className="form-group">
                    <label>Отправить приглашение по почте</label>
                    <input
                      type="email"
                      className="form-input"
                      placeholder="employee@domain.com"
                      value={inviteEmail}
                      onChange={e => setInviteEmail(e.target.value)}
                      required
                    />
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Пригласить</button>
                </form>

                <h3 style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>Активные инвайты</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {invites.length === 0 ? (
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Нет ожидающих инвайтов</p>
                  ) : (
                    invites.map(inv => (
                      <div key={inv.id} className="card" style={{ padding: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ minWidth: 0 }}>
                          <p style={{ fontSize: '13px', fontWeight: '500', overflow: 'hidden', textOverflow: 'ellipsis' }}>{inv.email}</p>
                          <span className={`badge ${inv.status === 'pending' ? 'badge-warning' : 'badge-neutral'}`} style={{ fontSize: '9px', padding: '2px 6px', marginTop: '4px' }}>
                            {inv.status === 'pending' ? 'Ожидает' : inv.status}
                          </span>
                        </div>
                        {inv.status === 'pending' && (
                          <button className="btn btn-danger btn-sm" onClick={() => handleCancelInvite(inv.id)}>Отменить</button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* DEPARTMENTS TAB */}
        {activeTab === 'departments' && (
          <div style={{ display: 'grid', gridTemplateColumns: isModerator ? '2fr 1fr' : '1fr', gap: '24px' }}>
            <div>
              <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Отделы и структуры</h2>
              {depts.length === 0 ? (
                <div className="empty-state">Отделы не созданы</div>
              ) : (
                <div className="card-grid">
                  {depts.map(d => (
                    <div key={d.id} className="card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <h3>{d.name}</h3>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button className="btn btn-secondary btn-sm" onClick={() => handleViewDept(d)}>Сотрудники</button>
                          {isModerator && (
                            <button className="btn btn-danger btn-sm" onClick={() => handleDeleteDept(d.id)}>Удалить</button>
                          )}
                        </div>
                      </div>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                        {d.description || 'Без описания'}
                      </p>
                      <p className="meta" style={{ marginTop: '12px' }}>Сотрудников: {d.member_count}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {isModerator && (
              <div>
                <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Добавить отдел</h2>
                <form onSubmit={handleCreateDept} className="card">
                  <div className="form-group">
                    <label>Название отдела</label>
                    <input className="form-input" placeholder="например, Отдел маркетинга" value={newDeptName} onChange={e => setNewDeptName(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label>Описание</label>
                    <textarea className="form-textarea" placeholder="Краткое описание функций" value={newDeptDesc} onChange={e => setNewDeptDesc(e.target.value)} />
                  </div>
                  <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Создать отдел</button>
                </form>
              </div>
            )}
          </div>
        )}

        {/* CHAT TAB */}
        {activeTab === 'chat' && (
          <div className="chat-container">
            <div className="chat-channels">
              {channels.map(c => (
                <button
                  key={c.id}
                  className={`chat-channel-btn${activeChannel?.id === c.id ? ' active' : ''}`}
                  onClick={() => setActiveChannel(c)}
                >
                  #{c.name}
                </button>
              ))}
              {isModerator && (
                <button className="btn btn-secondary btn-sm" onClick={() => setShowNewChannelModal(true)}>+ Создать канал</button>
              )}
            </div>

            {activeChannel ? (
              <>
                <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ fontSize: '15px', margin: 0 }}>#{activeChannel.name}</h3>
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{activeChannel.description || 'Нет описания темы'}</p>
                  </div>
                  {isModerator && (
                    <button className="btn btn-danger btn-sm" onClick={() => handleDeleteChannel(activeChannel.id)}>Удалить канал</button>
                  )}
                </div>

                <div className="chat-messages">
                  {messages.map(m => (
                    <div key={m.id} className={`chat-message${m.author_id === user.id ? ' own' : ''}${m.is_deleted ? ' deleted' : ''}`}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
                        <span className="author">{m.author_name}</span>
                        {isModerator && !m.is_deleted && (
                          <button
                            className="btn btn-link btn-sm"
                            style={{ padding: 0, border: 'none', background: 'none', color: 'var(--danger)', fontSize: '11px', cursor: 'pointer' }}
                            onClick={() => handleDeleteMessage(m.id)}
                          >
                            Удалить
                          </button>
                        )}
                      </div>
                      <div style={{ marginTop: '2px', wordBreak: 'break-word' }}>{m.content}</div>
                      <div className="time">{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>

                <form onSubmit={handleSendMessage} className="chat-input-area">
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Напишите сообщение..."
                    value={newMessage}
                    onChange={e => setNewMessage(e.target.value)}
                    required
                  />
                  <button type="submit" className="btn btn-primary">Отправить</button>
                </form>
              </>
            ) : (
              <div className="empty-state">Нет активных каналов чата</div>
            )}
          </div>
        )}

        {/* TASKS TAB */}
        {activeTab === 'tasks' && (
          <KanbanBoard orgId={orgId} members={members} isModerator={isModerator} />
        )}

        {/* FINANCE TAB */}
        {activeTab === 'finance' && (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
            <div>
              <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Журнал финансовых операций</h2>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Название</th>
                      <th>Тип</th>
                      <th>Сумма</th>
                      <th>Запросил</th>
                      <th>Статус</th>
                      {isModerator && <th>Действия</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {finance.map(f => (
                      <tr key={f.id}>
                        <td>
                          <p style={{ fontWeight: '600' }}>{f.title}</p>
                          <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{f.description}</p>
                        </td>
                        <td>
                          <span className={`badge ${f.category === 'income' ? 'badge-success' : 'badge-neutral'}`}>
                            {f.category === 'income' ? 'Доход' : 'Расход'}
                          </span>
                        </td>
                        <td style={{ fontWeight: '700', color: f.category === 'income' ? 'var(--success)' : 'var(--text-primary)' }}>
                          {f.category === 'income' ? '+' : '-'}{parseFloat(f.amount).toLocaleString('ru-RU')} ₽
                        </td>
                        <td>{f.creator_name}</td>
                        <td>
                          <span className={`badge ${
                            f.status === 'approved' ? 'badge-success' :
                            f.status === 'rejected' ? 'badge-danger' : 'badge-warning'
                          }`}>
                            {f.status === 'approved' ? 'Утверждено' :
                             f.status === 'rejected' ? 'Отклонено' : 'Ожидает'}
                          </span>
                        </td>
                        {isModerator && (
                          <td>
                            {f.status === 'pending' && (
                              <div className="actions-cell">
                                <button className="btn btn-success btn-sm" onClick={() => handleApproveFinance(f.id, 'approved')}>Да</button>
                                <button className="btn btn-danger btn-sm" onClick={() => handleApproveFinance(f.id, 'rejected')}>Нет</button>
                              </div>
                            )}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Создать заявку</h2>
              <form onSubmit={handleCreateFinance} className="card">
                <div className="form-group">
                  <label>Название операции</label>
                  <input className="form-input" placeholder="например, Закупка канцелярии" value={newFinTitle} onChange={e => setNewFinTitle(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Описание / Обоснование</label>
                  <textarea className="form-textarea" placeholder="Детали..." value={newFinDesc} onChange={e => setNewFinDesc(e.target.value)} />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Сумма (₽)</label>
                    <input type="number" step="0.01" className="form-input" placeholder="0.00" value={newFinAmount} onChange={e => setNewFinAmount(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label>Тип</label>
                    <select className="form-select" value={newFinCat} onChange={e => setNewFinCat(e.target.value)}>
                      <option value="expense">Расход</option>
                      <option value="income">Доход</option>
                    </select>
                  </div>
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '10px' }}>
                  Отправить на утверждение
                </button>
              </form>
            </div>
          </div>
        )}

        {/* ABSENCES TAB */}
        {activeTab === 'absences' && (
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
            <div>
              <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Календарь и список отсутствий</h2>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Сотрудник</th>
                      <th>Тип</th>
                      <th>Период</th>
                      <th>Причина</th>
                      <th>Статус</th>
                      {isModerator && <th>Модерация</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {absences.map(abs => (
                      <tr key={abs.id}>
                        <td style={{ fontWeight: '500' }}>{abs.user_name}</td>
                        <td>
                          <span className="badge badge-neutral">
                            {abs.absence_type === 'vacation' ? 'Отпуск' :
                             abs.absence_type === 'sick_leave' ? 'Больничный' :
                             abs.absence_type === 'business_trip' ? 'Командировка' :
                             abs.absence_type === 'remote' ? 'Удаленная работа' : 'Другое'}
                          </span>
                        </td>
                        <td style={{ fontSize: '12px' }}>
                          с {new Date(abs.start_date).toLocaleDateString('ru-RU')}
                          <br />по {new Date(abs.end_date).toLocaleDateString('ru-RU')}
                        </td>
                        <td style={{ color: 'var(--text-secondary)' }}>{abs.reason || '—'}</td>
                        <td>
                          <span className={`badge ${
                            abs.status === 'approved' ? 'badge-success' :
                            abs.status === 'rejected' ? 'badge-danger' : 'badge-warning'
                          }`}>
                            {abs.status === 'approved' ? 'Одобрено' :
                             abs.status === 'rejected' ? 'Отклонено' : 'Ожидает'}
                          </span>
                        </td>
                        {isModerator && (
                          <td>
                            {abs.status === 'pending' && (
                              <div className="actions-cell">
                                <button className="btn btn-success btn-sm" onClick={() => handleApproveAbsence(abs.id, 'approved')}>Одобрить</button>
                                <button className="btn btn-danger btn-sm" onClick={() => handleApproveAbsence(abs.id, 'rejected')}>Отклонить</button>
                              </div>
                            )}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Заявить об отсутствии</h2>
              <form onSubmit={handleCreateAbsence} className="card">
                <div className="form-group">
                  <label>Причина отсутствия</label>
                  <select className="form-select" value={newAbsType} onChange={e => setNewAbsType(e.target.value)}>
                    <option value="vacation">Отпуск</option>
                    <option value="sick_leave">Больничный</option>
                    <option value="business_trip">Командировка</option>
                    <option value="remote">Удаленная работа</option>
                    <option value="other">Другое</option>
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Начало</label>
                    <input type="date" className="form-input" value={newAbsStart} onChange={e => setNewAbsStart(e.target.value)} required />
                  </div>
                  <div className="form-group">
                    <label>Конец</label>
                    <input type="date" className="form-input" value={newAbsEnd} onChange={e => setNewAbsEnd(e.target.value)} required />
                  </div>
                </div>
                <div className="form-group">
                  <label>Пояснение (необязательно)</label>
                  <textarea className="form-textarea" placeholder="Причина или дополнительная информация..." value={newAbsReason} onChange={e => setNewAbsReason(e.target.value)} />
                </div>
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Отправить заявку</button>
              </form>
            </div>
          </div>
        )}

        {/* LOGS TAB */}
        {activeTab === 'logs' && (
          <div>
            <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Журнал действий в организации</h2>
            
            <div style={{ marginBottom: '16px', maxWidth: '400px' }}>
              <input
                type="text"
                className="form-input"
                placeholder="Поиск по имени, действию или сущности..."
                value={logsSearch}
                onChange={e => setLogsSearch(e.target.value)}
              />
            </div>

            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Время</th>
                    <th>Сотрудник</th>
                    <th>Действие</th>
                    <th>Тип сущности</th>
                    <th>Детали</th>
                  </tr>
                </thead>
                <tbody>
                  {orgLogs.map(log => (
                    <tr key={log.id}>
                      <td style={{ color: 'var(--text-muted)', fontSize: '12px', whiteSpace: 'nowrap' }}>
                        {new Date(log.created_at).toLocaleString('ru-RU')}
                      </td>
                      <td style={{ fontWeight: '500' }}>{log.user_name}</td>
                      <td>
                        <span className="badge badge-info">{log.action}</span>
                      </td>
                      <td>{log.entity_type}</td>
                      <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{log.details || '—'}</td>
                    </tr>
                  ))}
                  {orgLogs.length === 0 && (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                        Записей не найдено
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* SETTINGS TAB */}
        {activeTab === 'settings' && (
          <div style={{ maxWidth: '700px' }}>
            <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Параметры организации</h2>
            {isModerator ? (
              <form onSubmit={handleUpdateOrg} className="card" style={{ marginBottom: '24px' }}>
                <div className="form-group">
                  <label>Название организации</label>
                  <input className="form-input" value={editName} onChange={e => setEditName(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Описание</label>
                  <textarea className="form-textarea" value={editDesc} onChange={e => setEditDesc(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Категория</label>
                  <select className="form-select" value={editCategory} onChange={e => setEditCategory(e.target.value)}>
                    {ORG_CATEGORIES.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Сайт</label>
                    <input className="form-input" value={editWebsite} onChange={e => setEditWebsite(e.target.value)} placeholder="https://" />
                  </div>
                  <div className="form-group">
                    <label>Телефон</label>
                    <input className="form-input" value={editPhone} onChange={e => setEditPhone(e.target.value)} placeholder="+7" />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Адрес</label>
                    <input className="form-input" value={editAddress} onChange={e => setEditAddress(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label>Размер</label>
                    <input className="form-input" value={editSize} onChange={e => setEditSize(e.target.value)} placeholder="например, 10-50" />
                  </div>
                </div>
                <button type="submit" className="btn btn-primary">Сохранить изменения</button>
              </form>
            ) : (
              <div className="card" style={{ marginBottom: '24px' }}>
                <div className="form-group">
                  <label>Название организации</label>
                  <input className="form-input" value={org.name} readOnly />
                </div>
                <div className="form-group">
                  <label>Описание</label>
                  <textarea className="form-textarea" value={org.description || ''} readOnly />
                </div>
                <div className="form-group">
                  <label>Категория</label>
                  <input
                    className="form-input"
                    value={ORG_CATEGORIES.find(c => c.value === org.category)?.label || 'Другое'}
                    readOnly
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Сайт</label>
                    <input className="form-input" value={org.data?.website || ''} readOnly />
                  </div>
                  <div className="form-group">
                    <label>Телефон</label>
                    <input className="form-input" value={org.data?.phone || ''} readOnly />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Адрес</label>
                    <input className="form-input" value={org.data?.address || ''} readOnly />
                  </div>
                  <div className="form-group">
                    <label>Размер</label>
                    <input className="form-input" value={org.data?.size || ''} readOnly />
                  </div>
                </div>
              </div>
            )}

            {isModerator && (
              <div className="card" style={{ borderColor: 'var(--danger)' }}>
                <h3 style={{ color: 'var(--danger)' }}>Критическая зона</h3>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '14px' }}>
                  После удаления организации все данные о сотрудниках, отделах, финансах и чатах будут удалены безвозвратно.
                </p>
                <button className="btn btn-danger" onClick={handleDeleteOrg}>Удалить организацию</button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* MEMBER EDIT MODAL */}
      {showMemberModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowMemberModal(null)}>
          <div className="modal">
            <h2>Редактировать сотрудника: {showMemberModal.full_name}</h2>
            <form onSubmit={handleUpdateMember}>
              <div className="form-group">
                <label>Роль в организации</label>
                <select className="form-select" value={selectedRole} onChange={e => setSelectedRole(e.target.value)}>
                  <option value="employee">Сотрудник</option>
                  <option value="moderator">Модератор</option>
                </select>
              </div>
              <div className="form-group">
                <label>Должность</label>
                <input className="form-input" value={selectedPosition} onChange={e => setSelectedPosition(e.target.value)} placeholder="например, Главный аналитик" />
              </div>
              <div className="form-group">
                <label>Отдел</label>
                <select className="form-select" value={selectedDept} onChange={e => setSelectedDept(e.target.value)}>
                  <option value="">Без отдела</option>
                  {depts.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px' }}>
                <button type="button" className="btn btn-danger" onClick={() => handleRemoveMember(showMemberModal.id)}>Исключить</button>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button type="button" className="btn btn-secondary" onClick={() => setShowMemberModal(null)}>Отмена</button>
                  <button type="submit" className="btn btn-primary">Сохранить</button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DEPARTMENT MEMBERS MODAL */}
      {viewingDept && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setViewingDept(null)}>
          <div className="modal" style={{ maxWidth: 600 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ margin: 0 }}>Сотрудники: {viewingDept.name}</h2>
              <button className="btn btn-secondary btn-sm" onClick={() => setViewingDept(null)}>✕</button>
            </div>
            
            {deptMembers.length === 0 ? (
              <div className="empty-state">Нет сотрудников в этом отделе</div>
            ) : (
              <div className="table-container" style={{ maxHeight: 400, overflowY: 'auto' }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Имя</th>
                      <th>Email</th>
                      <th>Должность</th>
                      <th>Роль</th>
                    </tr>
                  </thead>
                  <tbody>
                    {deptMembers.map(m => (
                      <tr key={m.id}>
                        <td style={{ fontWeight: '500' }}>{m.full_name}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{m.email}</td>
                        <td>{m.position || '—'}</td>
                        <td>
                          <span className={`badge ${m.role === 'moderator' ? 'badge-info' : 'badge-neutral'}`}>
                            {m.role === 'moderator' ? 'Модератор' : 'Сотрудник'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* CREATE CHANNEL MODAL */}
      {showNewChannelModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowNewChannelModal(false)}>
          <div className="modal">
            <h2>Создать чат-канал</h2>
            <form onSubmit={handleCreateChannel}>
              <div className="form-group">
                <label>Название канала</label>
                <input className="form-input" placeholder="например, маркетинг" value={newChannelName} onChange={e => setNewChannelName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea className="form-textarea" placeholder="О чем этот канал?" value={newChannelDesc} onChange={e => setNewChannelDesc(e.target.value)} />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowNewChannelModal(false)}>Отмена</button>
                <button type="submit" className="btn btn-primary">Создать</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
