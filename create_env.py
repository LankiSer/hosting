#!/usr/bin/env python3
"""
Скрипт для создания .env файла с базовыми настройками
"""
import os

env_content = """# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hosting
DB_USER=postgres
DB_PASSWORD=admin

# RabbitMQ settings
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# JWT settings
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API settings
API_TITLE=Shared Hosting API
API_VERSION=1.0.0
"""

def create_env_file():
    """Создание .env файла"""
    env_path = ".env"
    
    if os.path.exists(env_path):
        print(f"Файл {env_path} уже существует!")
        return
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"Файл {env_path} успешно создан!")
        print("Не забудьте изменить SECRET_KEY в production!")
    except Exception as e:
        print(f"Ошибка при создании файла {env_path}: {e}")

if __name__ == "__main__":
    create_env_file() 