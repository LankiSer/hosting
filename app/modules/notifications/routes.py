from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.modules.notifications.schemas import NotificationResponse, NotificationCreate, NotificationAdminCreate, NotificationBroadcast
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
    query = select(Notification).where(Notification.user_id == current_user.auth_user_id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()
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


@router.post("/notifications/test", status_code=201)
async def create_test_notification(
    notification_type: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать тестовое уведомление для проверки"""
    
    test_notifications = {
        "info": {
            "title": "📢 Информационное уведомление",
            "message": "Это тестовое информационное уведомление для проверки системы уведомлений.",
            "type": "info"
        },
        "warning": {
            "title": "⚠️ Предупреждение",
            "message": "Внимание! Это тестовое предупреждение. Проверьте настройки вашего аккаунта.",
            "type": "warning"
        },
        "error": {
            "title": "❌ Ошибка",
            "message": "Произошла тестовая ошибка в системе. Обратитесь к администратору.",
            "type": "error"
        },
        "success": {
            "title": "✅ Успех",
            "message": "Операция успешно выполнена! Это тестовое уведомление об успехе.",
            "type": "success"
        }
    }
    
    if notification_type not in test_notifications:
        raise HTTPException(status_code=400, detail="Неподдерживаемый тип тестового уведомления")
    
    test_data = test_notifications[notification_type]
    
    # Создаем уведомление в базе данных
    notification = Notification(
        user_id=current_user.auth_user_id,
        title=test_data["title"],
        message=test_data["message"],
        type=test_data["type"]
    )
    
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    return {"detail": f"Тестовое уведомление типа '{notification_type}' создано", "notification_id": notification.id} 


@router.post("/notifications/broadcast", status_code=201)
async def broadcast_notification(
    notification: NotificationBroadcast,
    db: AsyncSession = Depends(get_db)
):
    """Отправить уведомление всем пользователям (без аутентификации)"""
    
    # Получаем всех пользователей
    from app.modules.auth.models import AuthUsers
    result = await db.execute(select(AuthUsers.auth_user_id))
    user_ids = result.scalars().all()
    
    created_notifications = []
    
    for user_id in user_ids:
        # Создаем уведомление для каждого пользователя
        db_notification = Notification(
            user_id=user_id,
            title=notification.title,
            message=notification.message,
            type=notification.type
        )
        
        db.add(db_notification)
        created_notifications.append(db_notification)
    
    await db.commit()
    
    return {
        "detail": f"Уведомление отправлено {len(created_notifications)} пользователям",
        "recipients_count": len(created_notifications),
        "notification_data": {
            "title": notification.title,
            "message": notification.message,
            "type": notification.type
        }
    }


@router.post("/notifications/admin/create", status_code=201)
async def create_notification_admin(
    notification: NotificationAdminCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать уведомление для пользователя (администраторский endpoint)"""
    
    # Создаем уведомление в базе данных
    db_notification = Notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        type=notification.type
    )
    
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    
    return {"detail": "Уведомление создано", "notification_id": db_notification.id}


@router.post("/notifications/admin/create-bulk", status_code=201)
async def create_bulk_notifications_admin(
    notifications: List[NotificationAdminCreate],
    db: AsyncSession = Depends(get_db)
):
    """Создать множественные уведомления для пользователей (администраторский endpoint)"""
    
    created_notifications = []
    
    for notification_data in notifications:
        # Создаем уведомление в базе данных
        db_notification = Notification(
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type
        )
        
        db.add(db_notification)
        created_notifications.append(db_notification)
    
    await db.commit()
    
    return {
        "detail": f"Создано {len(created_notifications)} уведомлений",
        "created_count": len(created_notifications)
    }


@router.post("/notifications/admin/broadcast", status_code=201)
async def broadcast_notification_admin(
    title: str,
    message: str,
    notification_type: str = "info",
    db: AsyncSession = Depends(get_db)
):
    """Отправить уведомление всем пользователям (администраторский endpoint)"""
    
    # Получаем всех пользователей
    from app.modules.auth.models import AuthUsers
    result = await db.execute(select(AuthUsers.auth_user_id))
    user_ids = result.scalars().all()
    
    created_notifications = []
    
    for user_id in user_ids:
        # Создаем уведомление для каждого пользователя
        db_notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        
        db.add(db_notification)
        created_notifications.append(db_notification)
    
    await db.commit()
    
    return {
        "detail": f"Уведомление отправлено {len(created_notifications)} пользователям",
        "recipients_count": len(created_notifications)
    } 