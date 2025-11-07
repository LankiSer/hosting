import logging
import secrets
import string
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations import ISPManagerError, extract_identifier, get_isp_client
from app.modules.auth.models import AuthUsers
from app.modules.auth.schemas import Token, UserLogin, UserRegister, UserResponse
from app.modules.hosting.models import HostingAccount
from app.modules.security.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)

logger = logging.getLogger(__name__)

ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _generate_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_ftp_username(base: str) -> str:
    sanitized = base.lower().replace(" ", "")
    sanitized = "".join(ch for ch in sanitized if ch.isalnum() or ch in {"-", "_"})
    if len(sanitized) < 3:
        sanitized = f"ftp{sanitized}".ljust(6, "0")
    suffix = secrets.token_hex(2)
    return f"{sanitized[:20]}_{suffix}"


class AuthService:
    """Сервис авторизации"""

    @staticmethod
    async def _ftp_username_exists(db: AsyncSession, username: str) -> bool:
        result = await db.execute(
            select(HostingAccount).where(HostingAccount.ftp_username == username)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def register_user(db: AsyncSession, user_data: UserRegister) -> UserResponse:
        """Регистрация нового пользователя"""

        existing_user = await db.execute(
            select(AuthUsers).where(AuthUsers.email == user_data.email)
        )
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже зарегистрирован",
            )

        existing_username = await db.execute(
            select(AuthUsers).where(AuthUsers.username == user_data.username)
        )
        if existing_username.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username уже занят",
            )

        auth_user = AuthUsers(
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
        )
        db.add(auth_user)
        await db.flush()

        # Подготовка FTP данных
        ftp_username = _generate_ftp_username(user_data.username)
        while await AuthService._ftp_username_exists(db, ftp_username):
            ftp_username = _generate_ftp_username(user_data.username)

        ftp_password = _generate_password(18)
        home_directory = f"{settings.ftp_root_path.rstrip('/')}/{auth_user.id}"

        isp_client = get_isp_client()

        try:
            account_payload = await isp_client.create_account(
                email=user_data.email,
                username=user_data.username,
                password=user_data.password,
                first_name=user_data.first_name or "",
                last_name=user_data.last_name or "",
                phone=user_data.phone or "",
            )

            account_id = extract_identifier(account_payload)
            auth_user.isp_account_id = account_id

            ftp_payload = await isp_client.create_ftp_user(
                account_id=account_id,
                username=ftp_username,
                password=ftp_password,
                home_directory=home_directory,
            )

            hosting_account = HostingAccount(
                user_id=auth_user.id,
                ftp_username=ftp_username,
                ftp_password=ftp_password,
                home_directory=home_directory,
                isp_ftp_id=extract_identifier(ftp_payload),
            )
            db.add(hosting_account)

            await db.commit()
        except ISPManagerError as exc:
            await db.rollback()
            logger.error("ISPmanager error during registration: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Не удалось создать аккаунт в панели управления",
            )
        except Exception:
            await db.rollback()
            logger.exception("Failed to register user")
            raise
        else:
            await db.refresh(auth_user)

        return UserResponse(
            user_id=auth_user.id,
            username=auth_user.username,
            email=auth_user.email,
            first_name=auth_user.first_name,
            last_name=auth_user.last_name,
            phone=auth_user.phone,
            email_verified=auth_user.email_verified,
            phone_verified=auth_user.phone_verified,
            created_at=auth_user.created_at,
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
            logger.warning(f"Попытка входа с несуществующим email: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль"
            )

        # 2. Проверить пароль
        if not verify_password(user_data.password, user.hashed_password):
            logger.warning(f"Неверный пароль для пользователя {user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль"
            )

        # 3. Проверить активность аккаунта
        if not user.is_active:
            logger.warning(f"Попытка входа в деактивированный аккаунт: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Аккаунт деактивирован"
            )

        # 4. Создать токены
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=30)
        
        token_data = {"sub": str(user.id), "email": user.email, "username": user.username}
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=refresh_token_expires
        )

        # 5. Обновить время последнего входа
        user.last_login = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Успешный вход пользователя {user.id}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> AuthUsers:
        """Получить пользователя по ID"""
        result = await db.execute(
            select(AuthUsers).where(AuthUsers.id == user_id)
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
        
        logger.info(f"Получен токен для проверки: {credentials.credentials[:20]}...")
        
        # Проверить и декодировать токен
        token_data = verify_token(credentials.credentials, "access")
        
        if token_data is None:
            logger.error("Токен недействителен")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Токен успешно декодирован, user_id: {token_data.get('user_id')}")
        
        # Получить пользователя из базы данных
        try:
            user = await AuthService.get_user_by_id(db, int(token_data["user_id"]))
            logger.info(f"Пользователь найден: {user.email}")
            return user
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def get_user_info(user: AuthUsers) -> UserResponse:
        """Получить информацию о пользователе"""
        return UserResponse(
            user_id=user.id,
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
    async def refresh_user_token(db: AsyncSession, refresh_token: str) -> Token:
        """Обновить JWT токен используя refresh токен"""
        # Проверить refresh токен
        token_data = verify_token(refresh_token, "refresh")
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недействительный refresh токен",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Получить пользователя
        try:
            user = await AuthService.get_user_by_id(db, int(token_data["user_id"]))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Создать новые токены
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=30)
        
        token_data_new = {"sub": str(user.id), "email": user.email, "username": user.username}
        
        new_access_token = create_access_token(
            data=token_data_new,
            expires_delta=access_token_expires
        )
        
        new_refresh_token = create_refresh_token(
            data=token_data_new,
            expires_delta=refresh_token_expires
        )
        
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
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