from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.users.schemas import UsersResponse, UsersUpdate
from app.modules.auth.routes import get_current_user
from typing import Optional

router = APIRouter()


@router.get("/users/me", response_model=UsersResponse)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Информация о текущем пользователе"""
    # TODO: Получить данные текущего пользователя
    # TODO: Включить связанные данные (client, limits)
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.patch("/users/me", response_model=UsersResponse)
async def update_my_profile(
    user_update: UsersUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновление профиля"""
    # TODO: Обновить данные пользователя
    # TODO: Проверить права доступа
    # TODO: Валидировать изменения
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/users/{user_id}", response_model=UsersResponse)
async def get_user_by_id(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Инфо по пользователю (для админов)"""
    # TODO: Проверить права администратора
    # TODO: Получить данные пользователя по ID
    # TODO: Проверить существование пользователя
    raise HTTPException(status_code=501, detail="Метод не реализован") 