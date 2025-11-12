import { useEffect, useMemo, useState } from 'react';
import { apiFetch, UserProfile } from '../lib/api';

type DashboardPageProps = {
  token: string;
  onLogout: () => void;
};

type UsageMetrics = {
  label: string;
  value: number;
  total: number;
  unit: string;
  color: 'blue' | 'orange';
};

type ServicePlan = {
  title: string;
  renewDate: string;
  status: 'active' | 'pending' | 'expired';
};

type Invoice = {
  amount: number;
  dueDate: string;
};

type Domain = {
  name: string;
  status: 'active' | 'pending' | 'expired';
  expiresAt: string;
};

export default function DashboardPage({ token, onLogout }: DashboardPageProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<UserProfile>('/users/me', { authToken: token })
      .then(setProfile)
      .catch((err) => {
        const status = (err as Error & { status?: number }).status ?? 0;
        if (status === 401 || status === 403) {
          onLogout();
        } else {
          setError(err instanceof Error ? err.message : 'Не удалось загрузить профиль');
        }
      });
  }, [onLogout, token]);

  const usageMetrics = useMemo<UsageMetrics[]>(
    () => [
      { label: 'Диск', value: 15, total: 50, unit: 'ГБ', color: 'blue' },
      { label: 'Трафик', value: 250, total: 1024, unit: 'ГБ', color: 'blue' },
      { label: 'Email-аккаунты', value: 10, total: 25, unit: 'шт', color: 'orange' },
      { label: 'Базы данных', value: 3, total: 10, unit: 'шт', color: 'blue' },
    ],
    []
  );

  const servicePlan = useMemo<ServicePlan>(
    () => ({
      title: 'Тариф «Профи»',
      renewDate: '15.12.2024',
      status: 'active',
    }),
    []
  );

  const invoice = useMemo<Invoice>(
    () => ({
      amount: 750,
      dueDate: '01.12.2024',
    }),
    []
  );

  const domains = useMemo<Domain[]>(
    () => [
      { name: 'example.com', status: 'active', expiresAt: '22.08.2025' },
      { name: 'my-project.net', status: 'active', expiresAt: '01.11.2024' },
    ],
    []
  );

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar__brand">HostPanel</div>
        <nav className="sidebar__menu">
          <a className="is-active" href="#overview">
            <span role="img" aria-label="Обзор">
              📊
            </span>
            Обзор
          </a>
          <a href="#domains">
            <span role="img" aria-label="Домены">
              🌐
            </span>
            Домены
          </a>
          <a href="#files">
            <span role="img" aria-label="Файлы">
              📁
            </span>
            Файлы
          </a>
          <a href="#databases">
            <span role="img" aria-label="Базы данных">
              🗄️
            </span>
            Базы данных
          </a>
          <a href="#billing">
            <span role="img" aria-label="Счета">
              💳
            </span>
            Счета
          </a>
        </nav>

        {profile ? (
          <div className="sidebar__profile">
            <div className="avatar">{initials(profile)}</div>
            <div>
              <div className="profile-name">{profile.first_name ?? profile.username}</div>
              <button type="button" onClick={onLogout}>
                Выйти
              </button>
            </div>
          </div>
        ) : null}
      </aside>

      <main className="dashboard__content">
        <header className="dashboard__header">
          <h1>Добро пожаловать, {profile?.first_name ?? profile?.username ?? 'клиент'}!</h1>
          <div className="header-tools">
            <input className="search-input" type="search" placeholder="Поиск доменов, файлов..." />
            <div className="balance">
              Баланс: <strong>1 250.00 ₽</strong>
              <button type="button">Пополнить</button>
            </div>
            <div className="header-icons">
              <span role="img" aria-label="Уведомления">
                🔔
              </span>
              <span role="img" aria-label="Справка">
                ❓
              </span>
            </div>
          </div>
        </header>

        {error ? <div className="banner banner--error">{error}</div> : null}

        <section className="card">
          <h2>Использование ресурсов</h2>
          <div className="metrics-grid">
            {usageMetrics.map((metric) => (
              <div key={metric.label} className="metric">
                <div className="metric__header">
                  <span>{metric.label}</span>
                  <strong>
                    {metric.value} / {metric.total} {metric.unit}
                  </strong>
                </div>
                <ProgressBar value={metric.value} total={metric.total} color={metric.color} />
              </div>
            ))}
          </div>
        </section>

        <section className="card card--grid">
          <div>
            <h2>Мои услуги</h2>
            <div className="plan-card">
              <div>
                <div className="plan-title">{servicePlan.title}</div>
                <div className="plan-meta">Продление: {servicePlan.renewDate}</div>
              </div>
              <span className="badge is-success">
                {servicePlan.status === 'active' ? 'Активен' : 'Ожидает оплаты'}
              </span>
              <button type="button" className="button button--ghost">
                Управлять
              </button>
            </div>
          </div>

          <div>
            <h2>Счета и оплата</h2>
            <div className="invoice-card">
              <div>
                <div className="invoice-amount">{invoice.amount.toFixed(2)} ₽</div>
                <div className="invoice-meta">Следующий платёж: {invoice.dueDate}</div>
              </div>
              <button type="button" className="button button--primary">
                Оплатить счёт
              </button>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card__header">
            <h2>Домены</h2>
            <button type="button" className="button button--ghost">
              Добавить домен
            </button>
          </div>
          <table className="domains-table">
            <thead>
              <tr>
                <th>Домен</th>
                <th>Статус</th>
                <th>Истекает</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {domains.map((domain) => (
                <tr key={domain.name}>
                  <td>{domain.name}</td>
                  <td>
                    <span className={`badge ${domain.status === 'active' ? 'is-success' : 'is-warning'}`}>
                      {domain.status === 'active' ? 'Активен' : 'Ожидает'}
                    </span>
                  </td>
                  <td>{domain.expiresAt}</td>
                  <td>
                    <button type="button" className="link-button">
                      Управлять
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card">
          <h2>Быстрые действия</h2>
          <div className="quick-actions">
            <button type="button">
              📁
              <span>Файлы</span>
            </button>
            <button type="button">
              🔐
              <span>FTP-аккаунты</span>
            </button>
            <button type="button">
              🗄️
              <span>Базы данных</span>
            </button>
            <button type="button">
              📧
              <span>Email</span>
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

type ProgressBarProps = {
  value: number;
  total: number;
  color: 'blue' | 'orange';
};

function ProgressBar({ value, total, color }: ProgressBarProps) {
  const percent = Math.min(100, Math.round((value / total) * 100));
  return (
    <div className="progress">
      <div className={`progress__bar progress__bar--${color}`} style={{ width: `${percent}%` }} />
    </div>
  );
}

function initials(profile: UserProfile) {
  const source = profile.first_name ?? profile.username ?? profile.email;
  const chunks = source.trim().split(/\s+/).slice(0, 2);
  return chunks
    .map((chunk) => chunk.charAt(0).toUpperCase())
    .join('')
    .padEnd(2, '•');
}

