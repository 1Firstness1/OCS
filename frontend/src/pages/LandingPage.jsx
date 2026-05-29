import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: '24px 48px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-secondary)' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--accent)', margin: 0 }}>OCS</h1>
        <div style={{ display: 'flex', gap: '16px' }}>
          <Link to="/login" className="btn btn-secondary">Вход</Link>
          <Link to="/register" className="btn btn-primary">Регистрация</Link>
        </div>
      </header>

      <main style={{ flex: 1, padding: '48px', maxWidth: '900px', margin: '0 auto', width: '100%' }}>
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <h2 style={{ fontSize: '36px', fontWeight: 'bold', marginBottom: '16px' }}>Добро пожаловать в OCS</h2>
          <p style={{ fontSize: '18px', color: 'var(--text-secondary)' }}>
            Универсальная платформа для управления организациями, задачами, сотрудниками и финансами.
          </p>
        </div>

        <div className="card-grid" style={{ gridTemplateColumns: '1fr', gap: '24px' }}>
          <div className="card">
            <h3 style={{ color: 'var(--accent)', fontSize: '20px', marginBottom: '12px' }}>1. Организации и Структура</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Создавайте организации и управляйте их структурой. Вы можете приглашать сотрудников, назначать им роли (сотрудник или модератор) и распределять их по отделам.
              Модераторы имеют расширенные права управления организацией и задачами.
            </p>
          </div>

          <div className="card">
            <h3 style={{ color: 'var(--accent)', fontSize: '20px', marginBottom: '12px' }}>2. Управление Задачами (Kanban)</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Создавайте доски для разных проектов. Модераторы могут создавать задачи, назначать исполнителей, устанавливать дедлайны и приоритеты.
              Исполнители могут отмечать выполнение чеклистов, писать комментарии и перемещать карточки по колонкам для отражения прогресса.
            </p>
          </div>

          <div className="card">
            <h3 style={{ color: 'var(--accent)', fontSize: '20px', marginBottom: '12px' }}>3. Чаты и Коммуникация</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Общайтесь с коллегами в реальном времени. Создавайте каналы для различных проектов или отделов.
            </p>
          </div>

          <div className="card">
            <h3 style={{ color: 'var(--accent)', fontSize: '20px', marginBottom: '12px' }}>4. Финансы и Аудит</h3>
            <p style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
              Ведите учет доходов и расходов организации. Каждое важное действие сотрудников (создание задач, удаление данных, изменение финансов) записывается в Журнал действий (Логи), доступный модераторам для контроля.
            </p>
          </div>
        </div>

        <div style={{ textAlign: 'center', marginTop: '48px', padding: '32px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)' }}>
          <h2 style={{ marginBottom: '16px' }}>Готовы начать?</h2>
          <Link to="/register" className="btn btn-primary" style={{ padding: '12px 24px', fontSize: '16px' }}>Создать аккаунт бесплатно</Link>
        </div>
      </main>

      <footer style={{ padding: '24px', textAlign: 'center', borderTop: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
        <p>&copy; 2026 OCS Platform. Все права защищены.</p>
      </footer>
    </div>
  );
}
