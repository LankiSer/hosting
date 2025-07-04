# 🔐 Руководство по реализации авторизации и регистрации

## 📋 Оглавление
1. [Общая архитектура](#общая-архитектура)
2. [Настройка JWT](#настройка-jwt)
3. [Хеширование паролей](#хеширование-паролей)
4. [Реализация регистрации](#реализация-регистрации)
5. [Реализация логина](#реализация-логина)
6. [Защита endpoints](#защита-endpoints)
7. [Middleware для авторизации](#middleware-для-авторизации)
8. [Примеры использования](#примеры-использования)

## 🏗️ Общая архитектура

### Схема авторизации:
```
1. Пользователь регистрируется → создается запись в БД с хешированным паролем
2. Пользователь входит → проверяется пароль → возвращается JWT токен
3. Для защищенных endpoints → проверяется JWT токен → определяется пользователь
4. Токен может быть отозван (logout) → добавляется в blacklist
```

### Структура файлов:
```
app/modules/auth/
├── routes.py        # API endpoints для auth
├── schemas.py       # Pydantic модели
├── service.py       # Бизнес-логика (создать)
├── security.py      # JWT и пароли (создать)
└── dependencies.py  # Зависимости для FastAPI (создать)
```

## 🔑 Настройка JWT

### 1. Создайте `app/modules/auth/security.py`:

```python
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройки JWT
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Получить хеш пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создать JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Проверить и декодировать токен"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": user_id, "email": payload.get("email")}
    except JWTError:
        return None
```

### 2. Обновите `.env` файл:
```env
SECRET_KEY=your-very-secret-key-change-in-production-32-chars-min
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 👤 Реализация модели пользователя

### 1. Добавьте в `app/core/models.py`:

```python
# Добавить к существующим моделям:
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from werkzeug.security import generate_password_hash, check_password_hash

class AuthUsers(Base):
    """Модель для авторизации пользователей"""
    __tablename__ = 'auth_users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default='now()')
    last_login = Column(DateTime)
    
    # Связь с основной таблицей users
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    user = relationship("Users", backref="auth_user")

# Или расширить существующую модель Users
# Добавить поля email, hashed_password к модели Users
```

## 📝 Реализация сервиса авторизации

### 1. Создайте `app/modules/auth/service.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.core.models import Users, Clients, AuthUsers
from app.modules.auth.security import get_password_hash, verify_password, create_access_token
from app.modules.auth.schemas import UserRegister, UserLogin, Token
from app.modules.notifications.producer import send_email_notification
from datetime import timedelta, datetime
import logging

logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    """Сервис авторизации"""
    
    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> dict:
        """Регистрация нового пользователя"""
        
        # 1. Проверить существование email
        existing_user = await db.execute(
            select(AuthUsers).where(AuthUsers.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован"
            )
        
        # 2. Проверить существование username
        existing_username = await db.execute(
            select(AuthUsers).where(AuthUsers.username == user_data.username)
        )
        if existing_username.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username уже занят"
            )
        
        # 3. Создать клиента
        client = Clients(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            email_verified=False,
            phone_verified=False
        )
        db.add(client)
        await db.flush()  # Получить client_id
        
        # 4. Создать пользователя
        user = Users(
            client_id=client.client_id,
            username=user_data.username
        )
        db.add(user)
        await db.flush()
        
        # 5. Создать запись авторизации
        auth_user = AuthUsers(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            user_id=user.user_id
        )
        db.add(auth_user)
        await db.commit()
        
        # 6. Отправить email подтверждения
        try:
            await send_email_notification(
                to=user_data.email,
                subject="Добро пожаловать в Shared Hosting!",
                body=f"Здравствуйте, {user_data.first_name}! Ваш аккаунт успешно создан."
            )
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")
        
        return {
            "user_id": user.user_id,
            "email": auth_user.email,
            "username": auth_user.username,
            "message": "Пользователь успешно зарегистрирован"
        }
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, user_data: UserLogin) -> Token:
        """Аутентификация пользователя"""
        
        # 1. Найти пользователя по email
        result = await db.execute(
            select(AuthUsers).where(AuthUsers.email == user_data.email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль"
            )
        
        # 2. Проверить пароль
        if not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль"
            )
        
        # 3. Проверить активность аккаунта
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Аккаунт деактивирован"
            )
        
        # 4. Создать токен
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.user_id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        # 5. Обновить время последнего входа
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
```

## 🔒 Создание зависимостей для защиты endpoints

### 1. Создайте `app/modules/auth/dependencies.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.auth.security import verify_token
from app.modules.auth.service import AuthService

security = HTTPBearer()

# Blacklist для отозванных токенов (в продакшене использовать Redis)
token_blacklist = set()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Dependency для получения текущего пользователя"""
    
    token = credentials.credentials
    
    # Проверить blacklist
    if token in token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен отозван"
        )
    
    # Проверить токен
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )
    
    return token_data


def logout_token(token: str):
    """Добавить токен в blacklist"""
    token_blacklist.add(token)
```

## 🧪 Тестирование

### 1. Тестовые запросы:

```bash
# Регистрация
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User"
  }'

# Логин
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

## 📝 Следующие шаги

1. **Создайте файлы**: `security.py`, `service.py`, `dependencies.py`
2. **Добавьте модель**: `AuthUsers` в `models.py`
3. **Создайте миграцию**: для новой таблицы
4. **Обновите роуты**: используйте `get_current_user` dependency
5. **Настройте email**: подтверждение регистрации

---

*Теперь у вас есть полная схема реализации авторизации! 🚀* 