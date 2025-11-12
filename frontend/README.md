# IspHosting Frontend

Минимальный фронт на Vite + React для авторизации, регистрации и демонстрационного дашборда поверх FastAPI-бэкенда.

## Старт разработки

```bash
cd frontend
npm install
npm run dev
```

По умолчанию dev-сервер запускается на `http://localhost:5173`. Для общения с API используется переменная `VITE_API_URL` (стандартно `http://192.168.1.153:8009`). Создайте файл `.env` (копия `env.example`) и подставьте URL вашего backend.

## Функциональность

- редирект с `/` на `/login`;
- форма входа (`/login`) вызывает `POST /auth/login`, загружает профиль `GET /users/me` и сохраняет токены в `localStorage`;
- форма регистрации (`/register`) отправляет `POST /auth/register` и перенаправляет на вход после успеха;
- защищённый дашборд (`/dashboard`) показывает приветственный экран, пример метрик и доменов, запрашивает профиль текущего пользователя и даёт кнопку выхода.

## Сборка и предпросмотр

```bash
npm run build
npm run preview
```

Собранные файлы лежат в `dist/`.

## Деплой

Скрипт `../scripts/deploy_frontend.sh` собирает проект и выгружает папку `dist/` на указанный сервер через `rsync`. Пример запуска:

```bash
./scripts/deploy_frontend.sh deploy@example.com /var/www/isp-hosting-frontend ./frontend/.env.prod
```

Убедитесь, что на сервере настроен nginx, который отдаёт статику из указанной директории и проксирует `/api` на FastAPI-бэкенд.

