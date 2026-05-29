import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';
import { useOutletContext } from 'react-router-dom';

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const { setOrgs } = useOutletContext() || { setOrgs: () => {} };
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [pendingInvites, setPendingInvites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState({ text: '', type: '' });

  useEffect(() => {
    setLoading(true);
    api.myPendingInvitations()
      .then(setPendingInvites)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleUpdate = async (e) => {
    e.preventDefault();
    setMsg({ text: '', type: '' });
    setSaving(true);
    try {
      await api.updateMe({ full_name: fullName, email });
      await refreshUser();
      setMsg({ text: 'Профиль успешно обновлен', type: 'success' });
    } catch (err) {
      setMsg({ text: 'Ошибка при обновлении профиля: ' + err.message, type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleAcceptInvite = async (invite) => {
    try {
      await api.acceptInvitation(invite.organization_id, invite.token);
      setPendingInvites(prev => prev.filter(i => i.id !== invite.id));
      alert('Приглашение принято!');
      // Update the organization list in sidebar/layout
      api.getOrganizations().then(setOrgs).catch(() => {});
    } catch (err) {
      alert('Не удалось принять приглашение: ' + err.message);
    }
  };

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Профиль пользователя</h1>
        <p>Управление личной информацией и приглашениями</p>
      </div>

      <div className="page-body" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', maxWidth: '1000px' }}>
        <div>
          <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Личные данные</h2>
          <form onSubmit={handleUpdate} className="card">
            {msg.text && (
              <div className={`alert ${msg.type === 'success' ? 'alert-success' : 'alert-error'}`}>
                {msg.text}
              </div>
            )}
            <div className="form-group">
              <label>Имя пользователя (логин)</label>
              <input className="form-input" value={user?.username || ''} disabled style={{ opacity: 0.7 }} />
            </div>
            <div className="form-group">
              <label>Полное имя</label>
              <input className="form-input" value={fullName} onChange={e => setFullName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" className="form-input" value={email} onChange={e => setEmail(e.target.value)} required />
            </div>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Сохранение...' : 'Сохранить изменения'}
            </button>
          </form>
        </div>

        <div>
          <h2 style={{ fontSize: '16px', marginBottom: '14px' }}>Входящие приглашения</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {pendingInvites.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                <p>У вас нет ожидающих приглашений</p>
              </div>
            ) : (
              pendingInvites.map(invite => (
                <div key={invite.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '14px' }}>Вас пригласили в организацию</h3>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Действительно до {new Date(invite.expires_at).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
                    <button className="btn btn-primary btn-sm" onClick={() => handleAcceptInvite(invite)}>Принять приглашение</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}
