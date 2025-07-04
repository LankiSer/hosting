from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.notifications.schemas import NotificationResponse
from app.modules.auth.routes import get_current_user
from typing import List, Optional

router = APIRouter()


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False
):
    """Список уведомлений пользователя"""
    # TODO: Получить уведомления пользователя
    # TODO: Фильтровать по прочитанным/непрочитанным
    # TODO: Применить пагинацию
    # TODO: Сортировать по дате
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.patch("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить уведомление как прочитанное"""
    # TODO: Проверить принадлежность уведомления
    # TODO: Обновить статус прочитанности
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.patch("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить все уведомления как прочитанные"""
    # TODO: Обновить все непрочитанные уведомления
    raise HTTPException(status_code=501, detail="Метод не реализован")


@router.get("/notifications/unread-count")
async def get_unread_notifications_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить количество непрочитанных уведомлений"""
    # TODO: Посчитать непрочитанные уведомления
    raise HTTPException(status_code=501, detail="Метод не реализован") 