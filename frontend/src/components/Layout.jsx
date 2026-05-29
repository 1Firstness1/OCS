import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import { api } from '../api';

const Icons = {
  home: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
  ),
  org: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
    </svg>
  ),
  admin: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
  ),
  profile: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
    </svg>
  ),
  logout: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  ),
  plus: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
    </svg>
  ),
  bell: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 7h18s-3 0-3-7"/>
      <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    </svg>
  ),
};

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

function roleLabel(role) {
  if (role === 'admin') return 'Администратор платформы';
  if (role === 'user') return 'Пользователь';
  return 'Гость';
}

function getInitials(name) {
  return name ? name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) : '?';
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [orgs, setOrgs] = useState([]);
  const [showCreateOrg, setShowCreateOrg] = useState(false);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgDesc, setNewOrgDesc] = useState('');
  const [createError, setCreateError] = useState('');
  const [newOrgCategory, setNewOrgCategory] = useState('other');
  const [newOrgWebsite, setNewOrgWebsite] = useState('');
  const [newOrgPhone, setNewOrgPhone] = useState('');
  const [newOrgAddress, setNewOrgAddress] = useState('');
  const [newOrgSize, setNewOrgSize] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    api.getOrganizations().then(setOrgs).catch(() => {});
  }, []);

  useEffect(() => {
    api.getNotifications(true)
      .then(data => setUnreadCount(data.length))
      .catch(() => {});
  }, []);

  const handleLogout = () => { logout(); navigate('/login'); };

  const handleCreateOrg = async (e) => {
    e.preventDefault();
    setCreateError('');
    try {
      const org = await api.createOrganization({
        name: newOrgName,
        description: newOrgDesc,
        category: newOrgCategory,
        data: {
          website: newOrgWebsite || null,
          phone: newOrgPhone || null,
          address: newOrgAddress || null,
          size: newOrgSize || null,
        }
      });
      setOrgs(prev => [...prev, org]);
      setShowCreateOrg(false);
      setNewOrgName('');
      setNewOrgDesc('');
      setNewOrgCategory('other');
      setNewOrgWebsite('');
      setNewOrgPhone('');
      setNewOrgAddress('');
      setNewOrgSize('');
      navigate(`/organizations/${org.id}`);
    } catch (err) {
      setCreateError(err.message);
    }
  };

  const openNotifications = async () => {
    try {
      const data = await api.getNotifications(false);
      setNotifications(data);
      setShowNotifications(true);
      setUnreadCount(data.filter(n => !n.is_read).length);
    } catch {
      setShowNotifications(true);
    }
  };

  const markNotificationRead = async (id) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {}
  };

  const markAllRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {}
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>OCS</h2>
          <p>Система управления организацией</p>
        </div>
        <nav className="sidebar-nav">
          <NavLink to="/" end className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            {Icons.home} Главная
          </NavLink>

          <button className="sidebar-link" onClick={openNotifications}>
            {Icons.bell}
            Уведомления
            {unreadCount > 0 && (
              <span className="badge badge-danger" style={{ marginLeft: 'auto' }}>{unreadCount}</span>
            )}
          </button>

          {orgs.length > 0 && <span className="sidebar-section">Организации</span>}
          {orgs.map(org => (
            <NavLink
              key={org.id}
              to={`/organizations/${org.id}`}
              className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
            >
              {Icons.org}
              <span style={{ overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{org.name}</span>
            </NavLink>
          ))}

          <button className="sidebar-link" onClick={() => setShowCreateOrg(true)}>
            {Icons.plus} Новая организация
          </button>

          <span className="sidebar-section" style={{ marginTop: 8 }}>Аккаунт</span>
          <NavLink to="/profile" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
            {Icons.profile} Профиль
          </NavLink>
          {user?.platform_role === 'admin' && (
            <NavLink to="/admin" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              {Icons.admin} Панель управления
            </NavLink>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="avatar">{getInitials(user?.full_name)}</div>
            <div className="info">
              <div className="name">{user?.full_name}</div>
              <div className="role">{roleLabel(user?.platform_role)}</div>
            </div>
          </div>
          <button className="sidebar-link" style={{ marginTop: 4 }} onClick={handleLogout}>
            {Icons.logout} Выйти
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Outlet context={{ orgs, setOrgs }} />
      </main>

      {showCreateOrg && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowCreateOrg(false)}>
          <div className="modal">
            <h2>Создать организацию</h2>
            <form onSubmit={handleCreateOrg}>
              {createError && <div className="alert alert-error">{createError}</div>}
              <div className="form-group">
                <label>Название</label>
                <input className="form-input" value={newOrgName} onChange={e => setNewOrgName(e.target.value)} required autoFocus />
              </div>
              <div className="form-group">
                <label>Описание</label>
                <textarea className="form-textarea" value={newOrgDesc} onChange={e => setNewOrgDesc(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Категория</label>
                <select className="form-select" value={newOrgCategory} onChange={e => setNewOrgCategory(e.target.value)}>
                  {ORG_CATEGORIES.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Сайт</label>
                  <input className="form-input" value={newOrgWebsite} onChange={e => setNewOrgWebsite(e.target.value)} placeholder="https://" />
                </div>
                <div className="form-group">
                  <label>Телефон</label>
                  <input className="form-input" value={newOrgPhone} onChange={e => setNewOrgPhone(e.target.value)} placeholder="+7" />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Адрес</label>
                  <input className="form-input" value={newOrgAddress} onChange={e => setNewOrgAddress(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Размер</label>
                  <input className="form-input" value={newOrgSize} onChange={e => setNewOrgSize(e.target.value)} placeholder="например, 10-50" />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateOrg(false)}>Отмена</button>
                <button type="submit" className="btn btn-primary">Создать</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showNotifications && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowNotifications(false)}>
          <div className="modal" style={{ maxWidth: 520 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>Уведомления</h2>
              <button className="btn btn-secondary btn-sm" onClick={markAllRead}>Прочитать все</button>
            </div>
            {notifications.length === 0 ? (
              <div className="empty-state" style={{ marginTop: 12 }}>Нет уведомлений</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
                {notifications.map(n => (
                  <div key={n.id} className="card" style={{ padding: 12, borderColor: n.is_read ? 'var(--border-color)' : 'var(--accent)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                      <div>
                        <div style={{ fontWeight: 600 }}>{n.title}</div>
                        {n.message && <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{n.message}</div>}
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>{new Date(n.created_at).toLocaleString('ru-RU')}</div>
                      </div>
                      {!n.is_read && (
                        <button className="btn btn-link btn-sm" style={{ color: 'var(--accent)', padding: 0 }} onClick={() => markNotificationRead(n.id)}>Прочитано</button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}