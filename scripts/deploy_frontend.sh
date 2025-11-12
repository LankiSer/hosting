#!/usr/bin/env bash
set -euo pipefail

# Скрипт для выгрузки собранного фронтенда на удалённый сервер.
# Требует установленный rsync и доступ по SSH с заранее настроенным ключом.

if [[ $# -lt 3 ]]; then
  cat <<'USAGE'
Использование: ./deploy_frontend.sh <ssh_user@host> <remote_path> <env_file>

  <ssh_user@host>  - адрес сервера (например, deploy@example.com)
  <remote_path>    - директория на сервере для фронта (например, /var/www/isp-hosting-frontend)
  <env_file>       - путь до локального .env файла для Vite (например, ./frontend/.env.prod)

Пример:
  ./deploy_frontend.sh deploy@example.com /var/www/isp-hosting-frontend ./frontend/.env.prod
USAGE
  exit 1
fi

SSH_TARGET="$1"
REMOTE_PATH="$2"
ENV_FILE="$3"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Файл окружения $ENV_FILE не найден" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

pushd "$PROJECT_ROOT/frontend" >/dev/null

echo "[1/4] Копируем файл окружения..."
cp "$ENV_FILE" .env

echo "[2/4] Устанавливаем зависимости..."
npm install --no-fund --no-audit

echo "[3/4] Сборка фронтенда..."
npm run build

echo "[4/4] Выгружаем dist на сервер..."
rsync -az --delete dist/ "$SSH_TARGET:$REMOTE_PATH/"

echo "Готово. Проверьте, что nginx обслуживает статику из $REMOTE_PATH."

popd >/dev/null

