from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.notifications.schemas import NotificationResponse, NotificationCreate
from app.modules.auth.routes import get_current_user
from typing import List, Optional
from app.modules.notifications.models import Notification
from sqlalchemy import select, func
from app.modules.notifications.producer import send_email_notification, send_sms_notification

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
    query = db.query(Notification).filter(Notification.user_id == current_user.auth_user_id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    notifications = await query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications


@router.patch("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить уведомление как прочитанное"""
    notification = await db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.auth_user_id:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    notification.is_read = True
    await db.commit()
    return


@router.patch("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Отметить все уведомления как прочитанные"""
    await db.execute(
        Notification.__table__.update()
        .where(Notification.user_id == current_user.auth_user_id)
        .values(is_read=True)
    )
    await db.commit()
    return


@router.get("/notifications/unread-count")
async def get_unread_notifications_count(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить количество непрочитанных уведомлений"""
    result = await db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == current_user.auth_user_id,
            Notification.is_read == False
        )
    )
    count = result.scalar()
    return {"unread_count": count}


@router.post("/notifications/send", status_code=201)
async def send_notification(
    notification: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Отправить уведомление пользователю через RabbitMQ (тестовый endpoint)"""
    # В зависимости от типа отправляем email или sms (можно расширить)
    if notification.type == "email":
        await send_email_notification(
            to=current_user.email,
            subject=notification.title,
            body=notification.message,
            user_id=current_user.auth_user_id
        )
    elif notification.type == "sms":
        await send_sms_notification(
            to=current_user.phone or "",
            text=notification.message,
            user_id=current_user.auth_user_id
        )
    else:
        # Можно добавить другие типы
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип уведомления")
    return {"detail": "Уведомление отправлено"} 