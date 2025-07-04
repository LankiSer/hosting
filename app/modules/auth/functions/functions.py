from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.core.models import Users, Clients
from app.modules.auth.models import AuthUsers
from app.modules.security.security import get_password_hash, verify_password, create_access_token, verify_token
from app.modules.auth.schemas import UserRegister, UserLogin, Token, UserResponse
from app.modules.notifications.producer import send_email_notification
from datetime import timedelta, datetime
import logging

logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = 30


class AuthService:
    """Сервис авторизации"""

    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> UserResponse:
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

        # 3. Создать пользователя авторизации
        auth_user = AuthUsers(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            is_active=True,
            email_verified=False,
            phone_verified=False
        )
        db.add(auth_user)
        await db.flush()  # Получить auth_user_id

        # 4. Создать клиента (для биллинга)
        client = Clients(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            email_verified=False,
            phone_verified=False
        )
        db.add(client)
        await db.flush()

        # 5. Создать системного пользователя (опционально)
        system_user = Users(
            client_id=client.client_id,
            username=user_data.username
        )
        db.add(system_user)
        await db.flush()

        # 6. Связать пользователя авторизации с системным пользователем
        auth_user.system_user_id = system_user.user_id
        
        await db.commit()

        # 7. Отправить email подтверждения
        try:
            await send_email_notification(
                to=user_data.email,
                subject="Добро пожаловать в Shared Hosting!",
                body=f"Здравствуйте, {user_data.first_name}! Ваш аккаунт успешно создан."
            )
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")

        return UserResponse(
            user_id=auth_user.auth_user_id,
            username=auth_user.username,
            email=auth_user.email,
            first_name=auth_user.first_name,
            last_name=auth_user.last_name,
            phone=auth_user.phone,
            email_verified=auth_user.email_verified,
            phone_verified=auth_user.phone_verified,
            created_at=auth_user.created_at
        )

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
            data={"sub": str(user.auth_user_id), "email": user.email, "username": user.username},
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

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> AuthUsers:
        """Получить пользователя по ID"""
        result = await db.execute(
            select(AuthUsers).where(AuthUsers.auth_user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        
        return user

    @staticmethod
    async def get_current_user_from_token(
        credentials: HTTPAuthorizationCredentials, 
        db: AsyncSession
    ) -> AuthUsers:
        """Получить текущего пользователя из JWT токена"""
        
        # Проверить и декодировать токен
        token_data = verify_token(credentials.credentials)
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Получить пользователя из базы данных
        try:
            user = await AuthService.get_user_by_id(db, int(token_data["user_id"]))
            return user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def get_user_info(user: AuthUsers) -> UserResponse:
        """Получить информацию о пользователе"""
        return UserResponse(
            user_id=user.auth_user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            created_at=user.created_at
        )

    @staticmethod
    async def refresh_user_token(user: AuthUsers) -> Token:
        """Обновить JWT токен пользователя"""
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.auth_user_id), "email": user.email, "username": user.username},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    @staticmethod
    async def logout_user(user: AuthUsers) -> dict:
        """Логаут пользователя"""
        # В текущей реализации JWT токены не хранятся в БД
        # Для полноценной реализации логаута нужно добавить черный список токенов
        logger.info(f"Пользователь {user.username} вышел из системы")
        return {"message": "Успешный выход из системы"}

    @staticmethod
    async def verify_email(db: AsyncSession, user_id: int) -> dict:
        """Подтвердить email пользователя"""
        user = await AuthService.get_user_by_id(db, user_id)
        user.email_verified = True
        await db.commit()
        
        return {"message": "Email подтвержден успешно"}

    @staticmethod
    async def verify_phone(db: AsyncSession, user_id: int) -> dict:
        """Подтвердить телефон пользователя"""
        user = await AuthService.get_user_by_id(db, user_id)
        user.phone_verified = True
        await db.commit()
        
        return {"message": "Телефон подтвержден успешно"}