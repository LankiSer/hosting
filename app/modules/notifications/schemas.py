from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class NotificationType(str, Enum):
    """Типы уведомлений"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationStatus(str, Enum):
    """Статусы уведомлений"""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class NotificationCreate(BaseModel):
    """Схема создания уведомления"""
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    user_id: int


class NotificationResponse(BaseModel):
    """Схема ответа уведомления"""
    notification_id: int
    title: str
    message: str
    type: NotificationType
    status: NotificationStatus
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True 