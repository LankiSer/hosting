# 🚀 Быстрый старт: Авторизация за 15 минут

## 📁 Шаг 1: Создайте необходимые файлы

### 1. `app/modules/auth/security.py`
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": int(user_id), "email": payload.get("email")}
    except JWTError:
        return None
```

### 2. `app/modules/auth/dependencies.py`
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.auth.security import verify_token

security = HTTPBearer()
token_blacklist = set()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    
    if token in token_blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен отозван"
        )
    
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен"
        )
    
    return token_data

def logout_token(token: str):
    token_blacklist.add(token)
```

## 📊 Шаг 2: Добавьте модель пользователя

### В `app/core/models.py` добавьте:
```python
class AuthUsers(Base):
    __tablename__ = 'auth_users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default='now()')
    last_login = Column(DateTime)
    
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    user = relationship("Users", backref="auth_user")
```

## 🔧 Шаг 3: Обновите роуты авторизации

### В `app/modules/auth/routes.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db import get_db
from app.core.models import AuthUsers, Users, Clients
from app.modules.auth.schemas import UserRegister, UserLogin, Token
from app.modules.auth.security import get_password_hash, verify_password, create_access_token
from app.modules.auth.dependencies import get_current_user, logout_token
from datetime import timedelta, datetime

router = APIRouter()
security = HTTPBearer()

@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Проверить существование email
    existing = await db.execute(select(AuthUsers).where(AuthUsers.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    # Создать клиента
    client = Clients(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email,
        phone=user_data.phone
    )
    db.add(client)
    await db.flush()
    
    # Создать пользователя
    user = Users(client_id=client.client_id, username=user_data.username)
    db.add(user)
    await db.flush()
    
    # Создать auth запись
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
    
    return {"message": "Пользователь зарегистрирован", "user_id": user.user_id}

@router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # Найти пользователя
    result = await db.execute(select(AuthUsers).where(AuthUsers.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Аккаунт деактивирован")
    
    # Создать токен
    access_token = create_access_token(
        data={"sub": str(user.user_id), "email": user.email},
        expires_delta=timedelta(minutes=30)
    )
    
    user.last_login = datetime.utcnow()
    await db.commit()
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=1800
    )

@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    logout_token(credentials.credentials)

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
```

## 🔐 Шаг 4: Защитите другие endpoints

### Пример использования в других роутах:
```python
from app.modules.auth.dependencies import get_current_user

@router.get("/users/me")
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user["user_id"]
    # Ваша логика здесь
    return {"user_id": user_id, "message": "Защищенный endpoint"}
```

## 🧪 Шаг 5: Тестирование

```bash
# 1. Регистрация
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User"
  }'

# 2. Логин
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# 3. Использование токена
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## ✅ Готово!

Теперь у вас работает:
- ✅ Регистрация пользователей
- ✅ JWT авторизация  
- ✅ Защита endpoints
- ✅ Логин/логаут

Переходите к реализации остальной логики! 🚀 