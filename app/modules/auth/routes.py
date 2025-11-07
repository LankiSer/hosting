from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.auth.functions.functions import AuthService
from app.modules.auth.models import AuthUsers
from app.modules.auth.schemas import RefreshTokenRequest, Token, UserLogin, UserRegister, UserResponse

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> AuthUsers:
    """Получить текущего пользователя по JWT токену"""
    return await AuthService.get_current_user_from_token(credentials, db)


@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация нового пользователя"""
    return await AuthService.register_user(db, user_data)


@router.post("/auth/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
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
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Обновить JWT токен"""
    return await AuthService.refresh_user_token(db, request.refresh_token)


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
    return await AuthService.verify_email(db, current_user.id)


@router.post("/auth/verify-phone")
async def verify_phone(
    current_user: AuthUsers = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подтвердить телефон пользователя"""
    return await AuthService.verify_phone(db, current_user.id)