from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base


class AuthUsers(Base):
    """Модель для авторизации пользователей"""
    __tablename__ = 'auth_users'
    
    auth_user_id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Персональные данные
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    
    # Статус аккаунта
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Связь с системным пользователем (опционально)
    system_user_id = Column(Integer, ForeignKey('users.user_id'), nullable=True)
    
    # Отношения
    system_user = relationship("Users", foreign_keys=[system_user_id])
    notifications = relationship('Notification', back_populates='user')
    support_tickets = relationship('SupportTicket', back_populates='user')
    support_sessions = relationship('SupportSession', back_populates='user')
    
    def __repr__(self):
        return f"<AuthUser(email='{self.email}', username='{self.username}')>" 