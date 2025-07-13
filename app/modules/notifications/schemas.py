from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Optional
from enum import Enum
import bleach


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
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    type: NotificationType = NotificationType.INFO
    user_id: int

    @validator('title', 'message')
    def sanitize_html(cls, v):
        # Удаляем HTML теги для безопасности
        return bleach.clean(v, tags=[], strip=True)


class NotificationAdminCreate(BaseModel):
    """Схема создания уведомления администратором"""
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    type: NotificationType = NotificationType.INFO
    user_id: int

    @validator('title', 'message')
    def sanitize_html(cls, v):
        # Удаляем HTML теги для безопасности
        return bleach.clean(v, tags=[], strip=True)


class NotificationBroadcast(BaseModel):
    """Схема создания уведомления для всех пользователей"""
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=2000)
    type: NotificationType = NotificationType.INFO

    @validator('title', 'message')
    def sanitize_html(cls, v):
        # Удаляем HTML теги для безопасности
        return bleach.clean(v, tags=[], strip=True)


class NotificationResponse(BaseModel):
    """Схема ответа уведомления"""
    id: int
    user_id: int
    title: str
    message: str
    type: NotificationType
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True 