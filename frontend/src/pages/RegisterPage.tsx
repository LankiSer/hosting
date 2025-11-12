import { FormEvent, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiFetch } from '../lib/api';

type AccountType = 'individual' | 'company';

const MIN_PASSWORD_LENGTH = 8;

export default function RegisterPage() {
  const navigate = useNavigate();
  const [accountType, setAccountType] = useState<AccountType>('individual');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const passwordStrength = useMemo(() => {
    if (!password) {
      return 0;
    }
    let score = 0;
    if (password.length >= MIN_PASSWORD_LENGTH) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[^a-zA-Z0-9]/.test(password)) score += 1;
    return score;
  }, [password]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    if (!acceptTerms) {
      setError('Необходимо принять условия использования');
      return;
    }

    setIsLoading(true);

    try {
      await apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          username: buildUsername(email, fullName),
          first_name: fullName,
        }),
      });

      setSuccess('Регистрация прошла успешно! Теперь войдите в систему.');
      setTimeout(() => navigate('/login', { replace: true }), 1200);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Не удалось завершить регистрацию';
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

        <h1 className="auth-title">Регистрация</h1>

        <div className="auth-tabs">
          <button
            type="button"
            className={`auth-tab ${accountType === 'individual' ? 'is-active' : ''}`}
            onClick={() => setAccountType('individual')}
          >
            Физическое лицо
          </button>
          <button
            type="button"
            className={`auth-tab ${accountType === 'company' ? 'is-active' : ''}`}
            onClick={() => setAccountType('company')}
          >
            Юридическое лицо
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="form-field">
            <span>{accountType === 'company' ? 'Название компании' : 'Логин'}</span>
            <input
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder={accountType === 'company' ? 'ООО «Пример»' : 'Выберите логин'}
              required
            />
          </label>

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
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Введите пароль"
              required
              autoComplete="new-password"
            />
            <PasswordStrengthIndicator score={passwordStrength} />
            <span className="field-hint">Минимум 8 символов, одна цифра, один спецсимвол.</span>
          </label>

          <label className="form-field">
            <span>Повторите пароль</span>
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Повторите пароль"
              required
              autoComplete="new-password"
            />
          </label>

          <label className="form-checkbox">
            <input
              type="checkbox"
              checked={acceptTerms}
              onChange={(event) => setAcceptTerms(event.target.checked)}
            />
            <span>
              Я принимаю условия использования и политику конфиденциальности.
            </span>
          </label>

          {error ? <div className="form-error">{error}</div> : null}
          {success ? <div className="form-success">{success}</div> : null}

          <button type="submit" className="button button--primary" disabled={isLoading}>
            {isLoading ? 'Отправляем…' : 'Зарегистрироваться'}
          </button>
        </form>

        <p className="auth-footer">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </div>
    </div>
  );
}

function buildUsername(email: string, fullName: string) {
  const fromName = fullName
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/gi, '_')
    .replace(/^_+|_+$/g, '');

  if (fromName.length >= 3) {
    return fromName.slice(0, 30);
  }

  const fromEmail = email.split('@')[0].replace(/[^a-z0-9]+/gi, '_');
  return (fromEmail || `user_${Date.now()}`).slice(0, 30);
}

type PasswordStrengthIndicatorProps = {
  score: number;
};

function PasswordStrengthIndicator({ score }: PasswordStrengthIndicatorProps) {
  return (
    <div className="password-strength" aria-hidden="true">
      {[0, 1, 2, 3].map((index) => (
        <span key={index} className={index < score ? 'is-active' : ''} />
      ))}
    </div>
  );
}

