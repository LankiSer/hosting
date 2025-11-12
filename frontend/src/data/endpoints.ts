export type HttpMethod = 'GET' | 'POST' | 'PATCH' | 'DELETE';

export type EndpointMeta = {
  id: string;
  method: HttpMethod;
  path: string;
  description: string;
  requiresAuth?: boolean;
  requiresBody?: boolean;
  pathParams?: string[];
};

export type EndpointGroup = {
  id: string;
  title: string;
  endpoints: EndpointMeta[];
};

export const ENDPOINT_GROUPS: EndpointGroup[] = [
  {
    id: 'general',
    title: 'Общие',
    endpoints: [
      {
        id: 'root',
        method: 'GET',
        path: '/',
        description: 'Корневой эндпоинт с метаданными API',
      },
      {
        id: 'health',
        method: 'GET',
        path: '/health',
        description: 'Проверка состояния API и версии',
      },
    ],
  },
  {
    id: 'auth',
    title: 'Авторизация',
    endpoints: [
      {
        id: 'auth-register',
        method: 'POST',
        path: '/auth/register',
        description: 'Регистрация нового пользователя',
        requiresBody: true,
      },
      {
        id: 'auth-login',
        method: 'POST',
        path: '/auth/login',
        description: 'Авторизация и выдача JWT',
        requiresBody: true,
      },
      {
        id: 'auth-me',
        method: 'GET',
        path: '/auth/me',
        description: 'Профиль текущего пользователя',
        requiresAuth: true,
      },
      {
        id: 'auth-refresh',
        method: 'POST',
        path: '/auth/refresh',
        description: 'Обновление access токена',
        requiresAuth: true,
        requiresBody: true,
      },
      {
        id: 'auth-logout',
        method: 'POST',
        path: '/auth/logout',
        description: 'Инвалидировать текущую сессию',
        requiresAuth: true,
      },
      {
        id: 'auth-verify-email',
        method: 'POST',
        path: '/auth/verify-email',
        description: 'Подтверждение email',
        requiresAuth: true,
      },
      {
        id: 'auth-verify-phone',
        method: 'POST',
        path: '/auth/verify-phone',
        description: 'Подтверждение телефона',
        requiresAuth: true,
      },
    ],
  },
  {
    id: 'users',
    title: 'Пользователи',
    endpoints: [
      {
        id: 'users-me-get',
        method: 'GET',
        path: '/users/me',
        description: 'Получить профиль текущего пользователя',
        requiresAuth: true,
      },
      {
        id: 'users-me-patch',
        method: 'PATCH',
        path: '/users/me',
        description: 'Обновить профиль текущего пользователя',
        requiresAuth: true,
        requiresBody: true,
      },
      {
        id: 'users-by-id',
        method: 'GET',
        path: '/users/{user_id}',
        description: 'Получить пользователя по ID (доступно владельцу)',
        requiresAuth: true,
        pathParams: ['user_id'],
      },
    ],
  },
  {
    id: 'domains',
    title: 'Домены',
    endpoints: [
      {
        id: 'domains-list',
        method: 'GET',
        path: '/domains',
        description: 'Список доменов пользователя',
        requiresAuth: true,
      },
      {
        id: 'domains-create',
        method: 'POST',
        path: '/domains',
        description: 'Создать домен и синхронизировать с ISPmanager',
        requiresAuth: true,
        requiresBody: true,
      },
      {
        id: 'domains-details',
        method: 'GET',
        path: '/domains/{domain_id}',
        description: 'Получить детали домена',
        requiresAuth: true,
        pathParams: ['domain_id'],
      },
      {
        id: 'domains-delete',
        method: 'DELETE',
        path: '/domains/{domain_id}',
        description: 'Удалить домен',
        requiresAuth: true,
        pathParams: ['domain_id'],
      },
      {
        id: 'domains-dns-create',
        method: 'POST',
        path: '/domains/{domain_id}/dns',
        description: 'Создать DNS запись',
        requiresAuth: true,
        requiresBody: true,
        pathParams: ['domain_id'],
      },
      {
        id: 'domains-dns-list',
        method: 'GET',
        path: '/domains/{domain_id}/dns',
        description: 'Получить DNS записи домена',
        requiresAuth: true,
        pathParams: ['domain_id'],
      },
    ],
  },
  {
    id: 'hosting',
    title: 'Хостинг',
    endpoints: [
      {
        id: 'hosting-ftp',
        method: 'GET',
        path: '/hosting/account/ftp',
        description: 'Получить данные FTP-аккаунта',
        requiresAuth: true,
      },
      {
        id: 'hosting-sites',
        method: 'GET',
        path: '/hosting/sites',
        description: 'Список сайтов пользователя',
        requiresAuth: true,
      },
      {
        id: 'hosting-sites-create',
        method: 'POST',
        path: '/hosting/sites',
        description: 'Создать сайт для пользователя',
        requiresAuth: true,
        requiresBody: true,
      },
      {
        id: 'hosting-site-details',
        method: 'GET',
        path: '/hosting/sites/{site_id}',
        description: 'Получить детали сайта',
        requiresAuth: true,
        pathParams: ['site_id'],
      },
      {
        id: 'hosting-site-delete',
        method: 'DELETE',
        path: '/hosting/sites/{site_id}',
        description: 'Удалить сайт',
        requiresAuth: true,
        pathParams: ['site_id'],
      },
    ],
  },
];

