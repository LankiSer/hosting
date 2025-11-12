# Деплой backend (FastAPI) с PostgreSQL

Инструкция по развёртыванию backend-приложения на сервере Linux (Ubuntu 22.04) с подключением PostgreSQL и nginx.

## 1. Подготовка сервера

1. Обновите систему:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
2. Установите системные пакеты:
   ```bash
   sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx git
   ```
3. Создайте пользователя для деплоя (пример):
   ```bash
   sudo useradd -m -s /bin/bash hosting
   sudo passwd hosting   # задайте пароль или настройте SSH-ключи
   sudo usermod -aG sudo hosting
   ```

## 2. Настройка PostgreSQL

1. Зайдите в консоль postgres:
   ```bash
   sudo -u postgres psql
   ```
2. Создайте базу и пользователя (сильные пароли!):
   ```sql
   CREATE DATABASE hosting;
   CREATE USER hosting_user WITH PASSWORD 'S3curePassw0rd';
   ALTER ROLE hosting_user SET client_encoding TO 'utf8';
   ALTER ROLE hosting_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE hosting_user SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE hosting TO hosting_user;
   \q
   ```
3. При необходимости откройте внешний доступ к БД (редактируйте `/etc/postgresql/14/main/pg_hba.conf` и `postgresql.conf`), либо используйте localhost.

## 3. Подготовка приложения

1. Выполните вход под пользователем деплоя и перейдите в домашнюю директорию:
   ```bash
   sudo su - hosting
   mkdir -p ~/apps && cd ~/apps
   git clone <URL-вашего-репозитория> hosting-app
   cd hosting-app
   ```
2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Создайте файл окружения `.env` на основе `app/core/config.py`:
   ```env
   db_host=127.0.0.1
   db_port=5432
   db_name=hosting
   db_user=hosting_user
   db_password=<пароль>
   secret_key=<случайная_строка>
   refresh_secret_key=<другая_строка>
   isp_api_base_url=https://isp.example.com # при необходимости
   ```
   Храните `.env` вне git, права `chmod 600 .env`.

## 4. Миграции базы данных

Перед первым запуском выполните миграции (в проекте используются SQL-файлы в `app/migrations/sql`):
```bash
source .venv/bin/activate
psql postgresql://hosting_user:<пароль>@127.0.0.1:5432/hosting -f app/migrations/sql/001__initial_schema.sql
```
Если подключены Alembic-миграции в `migrations/versions`, запускайте через `alembic upgrade head`.

## 5. Тестовый запуск

Проверьте, что приложение стартует локально (UVicorn):
```bash
source .venv/bin/activate
python run.py
```
По умолчанию сервер слушает `0.0.0.0:8000`. Остановите процесс `Ctrl+C` после проверки.

## 6. Конфигурация systemd

Создайте сервис для постоянного запуска backend:

1. Файл `/etc/systemd/system/hosting-api.service`:
   ```ini
   [Unit]
   Description=Hosting API (FastAPI + Uvicorn)
   After=network.target

   [Service]
   User=hosting
   Group=hosting
   WorkingDirectory=/home/hosting/apps/hosting-app
   EnvironmentFile=/home/hosting/apps/hosting-app/.env
   ExecStart=/home/hosting/apps/hosting-app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=5
   KillMode=process
   TimeoutStartSec=30

   [Install]
   WantedBy=multi-user.target
   ```
2. Примените конфигурацию:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable hosting-api
   sudo systemctl start hosting-api
   sudo systemctl status hosting-api
   ```

## 7. Настройка nginx

1. Создайте конфиг `/etc/nginx/sites-available/hosting-app`:
   ```nginx
   server {
     listen 80;
     server_name api.example.com;

     client_max_body_size 20m;

     location / {
       proxy_pass http://127.0.0.1:8000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_redirect off;
     }
   }
   ```
2. Активируйте конфиг и перезапустите nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/hosting-app /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```
3. Для HTTPS используйте certbot:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d api.example.com
   ```

## 8. Обновление приложения

```bash
cd ~/apps/hosting-app
git pull
source .venv/bin/activate
pip install -r requirements.txt
# примените новые миграции при необходимости
sudo systemctl restart hosting-api
```

## 9. Мониторинг и логи

- Логи приложения: `journalctl -u hosting-api -f`
- Логи nginx: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- Настройте ротацию логов или интеграцию с внешней системой (ELK, Loki).

## 10. Резервное копирование

Регулярно делайте резервные копии базы данных:
```bash
pg_dump postgresql://hosting_user:<пароль>@127.0.0.1:5432/hosting | gzip > /backups/hosting_$(date +%F).sql.gz
```

По необходимости автоматизируйте задачу cron’ом.

