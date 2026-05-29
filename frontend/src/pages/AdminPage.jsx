import { useState, useEffect } from 'react';
import { api } from '../api';
import { useAuth } from '../context/AuthContext';

export default function AdminPage() {
  const { user: currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [orgs, setOrgs] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reauthRequired, setReauthRequired] = useState(true);
  const [reauthPassword, setReauthPassword] = useState('');
  const [reauthError, setReauthError] = useState('');

  // Edit user modal state
  const [showEditUserModal, setShowEditUserModal] = useState(null);
  const [editFullName, setEditFullName] = useState('');
  const [editEmail, setEditEmail] = useState('');
  const [editRole, setEditRole] = useState('user');
  const [editIsActive, setEditIsActive] = useState(true);

  // Org logs modal state
  const [viewingOrgLogs, setViewingOrgLogs] = useState(null);
  const [orgLogs, setOrgLogs] = useState([]);
  const [orgLogsSearch, setOrgLogsSearch] = useState('');

  useEffect(() => {
    if (!currentUser || currentUser.platform_role !== 'admin') return;
    const lastReauth = localStorage.getItem('ocs_admin_reauth_at');
    const ttlMs = 10 * 60 * 1000;
    if (lastReauth && Date.now() - Number(lastReauth) < ttlMs) {
      setReauthRequired(false);
    } else {
      setReauthRequired(true);
      setLoading(false);
    }
  }, [currentUser]);

  useEffect(() => {
    if (reauthRequired || currentUser?.platform_role !== 'admin') return;
    setLoading(true);
    Promise.all([
      api.adminGetStats(),
      api.adminGetUsers(''),
      api.adminGetOrganizations(),
      api.adminGetAuditLog(),
    ])
      .then(([statsData, usersData, orgsData, auditData]) => {
        setStats(statsData);
        setUsers(usersData);
        setOrgs(orgsData);
        setAuditLogs(auditData);
      })
      .catch(err => alert('Ошибка загрузки административных данных: ' + err.message))
      .finally(() => setLoading(false));
  }, [reauthRequired, currentUser]);

  const handleReauth = async (e) => {
    e.preventDefault();
    setReauthError('');
    try {
      await api.reauth(reauthPassword);
      localStorage.setItem('ocs_admin_reauth_at', String(Date.now()));
      setReauthPassword('');
      setReauthRequired(false);
    } catch (err) {
      setReauthError('Неверный пароль');
    }
  };

  const handleSearchUsers = async (e) => {
    e.preventDefault();
    try {
      const results = await api.adminGetUsers(searchQuery);
      setUsers(results);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleOpenEditUser = (user) => {
    setShowEditUserModal(user);
    setEditFullName(user.full_name);
    setEditEmail(user.email);
    setEditRole(user.platform_role);
    setEditIsActive(user.is_active);
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      const updated = await api.adminUpdateUser(showEditUserModal.id, {
        full_name: editFullName,
        email: editEmail,
        platform_role: editRole,
        is_active: editIsActive,
      });
      setUsers(prev => prev.map(u => u.id === updated.id ? updated : u));
      setShowEditUserModal(null);
      // Refresh audit logs
      api.adminGetAuditLog().then(setAuditLogs).catch(() => {});
      // Refresh stats
      api.adminGetStats().then(setStats).catch(() => {});
    } catch (err) {
      alert('Ошибка при обновлении пользователя: ' + err.message);
    }
  };

  const handleDeactivateUser = async (userId) => {
    if (!confirm('Вы действительно хотите деактивировать этого пользователя? Он потеряет доступ к платформе.')) return;
    try {
      await api.adminDeactivateUser(userId);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: false } : u));
      api.adminGetAuditLog().then(setAuditLogs).catch(() => {});
      api.adminGetStats().then(setStats).catch(() => {});
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteOrganization = async (orgId) => {
    if (!confirm('Удалить организацию? Она будет деактивирована.')) return;
    try {
      await api.adminDeleteOrganization(orgId);
      setOrgs(prev => prev.map(o => o.id === orgId ? { ...o, is_active: false } : o));
      api.adminGetAuditLog().then(setAuditLogs).catch(() => {});
      api.adminGetStats().then(setStats).catch(() => {});
    } catch (err) {
      alert(err.message);
    }
  };

  const handleOpenOrgLogs = async (org) => {
    setViewingOrgLogs(org);
    setOrgLogsSearch('');
    try {
      const logs = await api.adminGetOrgLogs(org.id, '');
      setOrgLogs(logs);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSearchOrgLogs = async (e) => {
    e.preventDefault();
    try {
      const logs = await api.adminGetOrgLogs(viewingOrgLogs.id, orgLogsSearch);
      setOrgLogs(logs);
    } catch (err) {
      alert(err.message);
    }
  };

  if (!currentUser || currentUser.platform_role !== 'admin') {
    return <div className="page-body"><div className="alert alert-error">Доступ только для администраторов платформы</div></div>;
  }

  if (reauthRequired) {
    return (
      <div className="page-body" style={{ maxWidth: 420 }}>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Подтверждение входа</h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Введите пароль для доступа к панели администратора.</p>
          {reauthError && <div className="alert alert-error">{reauthError}</div>}
          <form onSubmit={handleReauth}>
            <div className="form-group">
              <label>Пароль</label>
              <input
                type="password"
                className="form-input"
                value={reauthPassword}
                onChange={e => setReauthPassword(e.target.value)}
                autoFocus
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>Подтвердить</button>
          </form>
        </div>
      </div>
    );
  }

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Панель администратора</h1>
        <p>Управление платформой, организациями и аудит критических действий</p>
        <div className="tabs" style={{ marginTop: '16px', marginBottom: 0 }}>
          <button className={`tab${activeTab === 'users' ? ' active' : ''}`} onClick={() => setActiveTab('users')}>Пользователи</button>
          <button className={`tab${activeTab === 'organizations' ? ' active' : ''}`} onClick={() => setActiveTab('organizations')}>Организации</button>
          <button className={`tab${activeTab === 'audit' ? ' active' : ''}`} onClick={() => setActiveTab('audit')}>Аудит действий</button>
        </div>
      </div>

      <div className="page-body">
        {/* STATS OVERVIEW */}
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <p className="label">Всего пользователей</p>
              <h2 className="value">{stats.total_users}</h2>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Активных: {stats.active_users}</p>
            </div>
            <div className="stat-card">
              <p className="label">Всего организаций</p>
              <h2 className="value">{stats.total_organizations}</h2>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Активных: {stats.active_organizations}</p>
            </div>
          </div>
        )}

        {/* USERS TAB */}
        {activeTab === 'users' && (
          <div>
            <form onSubmit={handleSearchUsers} className="search-box" style={{ marginBottom: '16px', maxWidth: '400px' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                type="text"
                className="form-input"
                placeholder="Поиск по имени, логину или email..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </form>

            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Имя</th>
                    <th>Имя пользователя</th>
                    <th>Email</th>
                    <th>Роль</th>
                    <th>Статус</th>
                    <th>Зарегистрирован</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id}>
                      <td style={{ fontWeight: '500' }}>{u.full_name}</td>
                      <td>{u.username}</td>
                      <td>{u.email}</td>
                      <td>
                        <span className={`badge ${u.platform_role === 'admin' ? 'badge-danger' : 'badge-neutral'}`}>
                          {u.platform_role === 'admin' ? 'Админ платформы' : 'Пользователь'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${u.is_active ? 'badge-success' : 'badge-danger'}`}>
                          {u.is_active ? 'Активен' : 'Заблокирован'}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                        {new Date(u.created_at).toLocaleDateString('ru-RU')}
                      </td>
                      <td>
                        <div className="actions-cell">
                          <button className="btn btn-secondary btn-sm" onClick={() => handleOpenEditUser(u)}>Изменить</button>
                          {u.is_active && u.id !== currentUser.id && (
                            <button className="btn btn-danger btn-sm" onClick={() => handleDeactivateUser(u.id)}>Блокировать</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ORGANIZATIONS TAB */}
        {activeTab === 'organizations' && (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Название</th>
                  <th>Владелец</th>
                  <th>Участников</th>
                  <th>Статус</th>
                  <th>Дата создания</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {orgs.map(o => (
                  <tr key={o.id}>
                    <td style={{ fontWeight: '600' }}>
                      <p style={{ margin: 0 }}>{o.name}</p>
                      <p style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '400' }}>{o.description}</p>
                    </td>
                    <td>{o.owner_name}</td>
                    <td>{o.member_count}</td>
                    <td>
                      <span className={`badge ${o.is_active ? 'badge-success' : 'badge-neutral'}`}>
                        {o.is_active ? 'Активна' : 'Удалена'}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                      {new Date(o.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td>
                      <div className="actions-cell">
                        <button className="btn btn-secondary btn-sm" onClick={() => handleOpenOrgLogs(o)}>Логи</button>
                        {o.is_active && (
                          <button className="btn btn-danger btn-sm" onClick={() => handleDeleteOrganization(o.id)}>Удалить</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* AUDIT LOG TAB */}
        {activeTab === 'audit' && (
          <div>
            <h2 style={{ fontSize: '15px', marginBottom: '12px' }}>Журнал критических действий (Последние 200 событий)</h2>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Время</th>
                    <th>Исполнитель</th>
                    <th>Действие</th>
                    <th>Тип сущности</th>
                    <th>ID сущности</th>
                    <th>Детали</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map(log => (
                    <tr key={log.id}>
                      <td style={{ color: 'var(--text-muted)', fontSize: '12px', whiteSpace: 'nowrap' }}>
                        {new Date(log.created_at).toLocaleString('ru-RU')}
                      </td>
                      <td style={{ fontWeight: '500' }}>{log.user_name}</td>
                      <td>
                        <span className="badge badge-info">{log.action}</span>
                      </td>
                      <td>{log.entity_type}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-secondary)' }}>{log.entity_id || '—'}</td>
                      <td style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{log.details || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* EDIT USER MODAL */}
      {showEditUserModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowEditUserModal(null)}>
          <div className="modal">
            <h2>Редактировать пользователя: {showEditUserModal.username}</h2>
            <form onSubmit={handleUpdateUser}>
              <div className="form-group">
                <label>Полное имя</label>
                <input className="form-input" value={editFullName} onChange={e => setEditFullName(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" className="form-input" value={editEmail} onChange={e => setEditEmail(e.target.value)} required />
              </div>
              <div className="form-group">
                <label>Роль на платформе</label>
                <select className="form-select" value={editRole} onChange={e => setEditRole(e.target.value)}>
                  <option value="user">Пользователь</option>
                  <option value="admin">Администратор платформы</option>
                </select>
              </div>
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '12px' }}>
                <input
                  type="checkbox"
                  id="edit-is-active"
                  checked={editIsActive}
                  onChange={e => setEditIsActive(e.target.checked)}
                  disabled={showEditUserModal.id === currentUser.id}
                />
                <label htmlFor="edit-is-active" style={{ margin: 0, cursor: 'pointer' }}>Пользователь активен (разблокирован)</label>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowEditUserModal(null)}>Отмена</button>
                <button type="submit" className="btn btn-primary">Сохранить</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ORG LOGS MODAL */}
      {viewingOrgLogs && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setViewingOrgLogs(null)}>
          <div className="modal" style={{ maxWidth: 800 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h2 style={{ margin: 0 }}>Логи организации: {viewingOrgLogs.name}</h2>
              <button className="btn btn-secondary btn-sm" onClick={() => setViewingOrgLogs(null)}>✕</button>
            </div>
            
            <form onSubmit={handleSearchOrgLogs} className="search-box" style={{ marginBottom: '16px', maxWidth: '400px' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <input
                type="text"
                className="form-input"
                placeholder="Поиск по логам..."
                value={orgLogsSearch}
                onChange={e => setOrgLogsSearch(e.target.value)}
              />
            </form>

            <div className="table-container" style={{ maxHeight: 400, overflowY: 'auto' }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Время</th>
                    <th>Пользователь</th>
                    <th>Действие</th>
                    <th>Сущность</th>
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
                      <td><span className="badge badge-info">{log.action}</span></td>
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
        </div>
      )}
    </>
  );
}