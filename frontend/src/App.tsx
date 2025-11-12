import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import { AuthTokens, UserProfile } from './lib/api';

type AuthState = {
  tokens: AuthTokens;
  profile: UserProfile;
};

const STORAGE_KEY = 'isp-hosting-auth';

function usePersistedAuth() {
  const [auth, setAuth] = useState<AuthState | null>(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as AuthState;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    if (auth) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [auth]);

  return { auth, setAuth };
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthRouter />
    </BrowserRouter>
  );
}

function AuthRouter() {
  const { auth, setAuth } = usePersistedAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = Boolean(auth?.tokens?.access_token);

  useEffect(() => {
    if (!isAuthenticated && location.pathname !== '/login' && location.pathname !== '/register') {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, location.pathname, navigate]);

  const handleLogin = (tokens: AuthTokens, profile: UserProfile) => {
    setAuth({ tokens, profile });
    navigate('/dashboard', { replace: true });
  };

  const handleLogout = () => {
    setAuth(null);
    navigate('/login', { replace: true });
  };

  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/dashboard"
        element={
          isAuthenticated && auth ? (
            <DashboardPage token={auth.tokens.access_token} onLogout={handleLogout} />
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

