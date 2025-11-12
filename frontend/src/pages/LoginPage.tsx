import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch, AuthTokens, UserProfile } from '../lib/api';

type LoginPageProps = {
  onLogin: (tokens: AuthTokens, profile: UserProfile) => void;
};

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const tokens = await apiFetch<AuthTokens>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      const profile = await apiFetch<UserProfile>('/users/me', {
        authToken: tokens.access_token,
      });

      onLogin(tokens, profile);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Не удалось войти';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-brand">
          <div className="auth-logo">◆</div>
          <span>Shared Hosting</span>
        </div>

        <h1 className="auth-title">Вход</h1>
        <p className="auth-subtitle">Используйте email и пароль, чтобы войти в панель управления.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Введите ваш email"
              required
              autoComplete="email"
            />
          </label>

          <label className="form-field">
            <span>Пароль</span>
            <div className="password-field">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Введите пароль"
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
            <span className="field-hint">Минимум 8 символов, одна цифра, один спецсимвол.</span>
          </label>

          {error ? <div className="form-error">{error}</div> : null}

          <button type="submit" className="button button--primary" disabled={isLoading}>
            {isLoading ? 'Входим…' : 'Войти'}
          </button>
        </form>

        <p className="auth-footer">
          Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </div>
    </div>
  );
}

