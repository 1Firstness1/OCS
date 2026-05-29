import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api';

function getInitials(name) {
  return name ? name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) : '?';
}

function OrgCard({ org, onClick }) {
  return (
    <div className="card" style={{ cursor: 'pointer' }} onClick={onClick}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 10 }}>
        <div style={{
          width: 42, height: 42, borderRadius: 10,
          background: 'linear-gradient(135deg,#4f68e8,#7c3aed)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 700, fontSize: 18, color: '#fff', flexShrink: 0
        }}>
          {org.name[0].toUpperCase()}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{org.name}</h3>
          <p className="meta">{org.member_count} {memberWord(org.member_count)}</p>
        </div>
      </div>
      {org.description && (
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
          {org.description}
        </p>
      )}
    </div>
  );
}

function memberWord(n) {
  if (n % 10 === 1 && n % 100 !== 11) return 'участник';
  if ([2,3,4].includes(n % 10) && ![12,13,14].includes(n % 100)) return 'участника';
  return 'участников';
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [orgs, setOrgs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getOrganizations()
      .then(setOrgs)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading"><div className="spinner" /></div>;

  return (
    <>
      <div className="page-header">
        <h1>Главная</h1>
        <p>Добро пожаловать, {user?.full_name}</p>
      </div>
      <div className="page-body">
        {orgs.length === 0 ? (
          <div className="empty-state">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="2" y="7" width="20" height="14" rx="2"/>
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
            </svg>
            <p>Вы пока не состоите ни в одной организации</p>
            <p style={{ fontSize: 13 }}>Создайте организацию через боковое меню или примите приглашение</p>
          </div>
        ) : (
          <>
            <h2 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 14, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Мои организации — {orgs.length}
            </h2>
            <div className="card-grid">
              {orgs.map(org => (
                <OrgCard key={org.id} org={org} onClick={() => navigate(`/organizations/${org.id}`)} />
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}
