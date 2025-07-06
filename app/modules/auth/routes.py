from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.auth.schemas import UserRegister, UserLogin, UserResponse, Token
from app.modules.auth.functions.functions import AuthService
from app.modules.auth.models import AuthUsers
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

router = APIRouter()
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> AuthUsers:
    """Получить текущего пользователя по JWT токену"""
    return await AuthService.get_current_user_from_token(credentials, db)


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """Регистрация нового пользователя"""
    return await AuthService.register_user(db, user_data)


@router.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(
    request: Request,
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Вход по email и паролю (JWT токен)"""
    return await AuthService.authenticate_user(db, user_data)


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AuthUsers = Depends(get_current_user)
):
    """Получить информацию о текущем пользователе"""
    return await AuthService.get_user_info(current_user)


@router.post("/auth/refresh", response_model=Token)
async def refresh_token(
    current_user: AuthUsers = Depends(get_current_user)
):
    """Обновить JWT токен"""
    return await AuthService.refresh_user_token(current_user)


@router.post("/auth/logout")
async def logout(
    current_user: AuthUsers = Depends(get_current_user)
):
    """Выход из системы"""
    return await AuthService.logout_user(current_user)


@router.post("/auth/verify-email")
async def verify_email(
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подтвердить email пользователя"""
    return await AuthService.verify_email(db, current_user.auth_user_id)


@router.post("/auth/verify-phone")
async def verify_phone(
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подтвердить телефон пользователя"""
    return await AuthService.verify_phone(db, current_user.auth_user_id) 