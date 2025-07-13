from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class TicketStatus(enum.Enum):
    """Статусы тикетов поддержки"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MessageType(enum.Enum):
    """Типы сообщений в чате"""
    USER = "user"
    BOT = "bot"
    OPERATOR = "operator"


class SessionStatus(enum.Enum):
    """Статусы сессий чата"""
    ACTIVE = "active"
    WAITING_OPERATOR = "waiting_operator"
    WITH_OPERATOR = "with_operator"
    CLOSED = "closed"


class SupportTicket(Base):
    """Тикет поддержки"""
    __tablename__ = 'support_tickets'
    
    ticket_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('auth_users.auth_user_id'), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(Integer, default=1)  # 1-низкий, 2-средний, 3-высокий
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime, nullable=True)
    assigned_operator_id = Column(Integer, nullable=True)  # ID оператора
    
    # Связи
    user = relationship('AuthUsers', back_populates='support_tickets')
    messages = relationship('SupportMessage', back_populates='ticket')
    session = relationship('SupportSession', back_populates='ticket', uselist=False)


class SupportMessage(Base):
    """Сообщение в чате поддержки"""
    __tablename__ = 'support_messages'
    
    message_id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey('support_tickets.ticket_id'), nullable=False)
    session_id = Column(Integer, ForeignKey('support_sessions.session_id'), nullable=True)
    message_type = Column(Enum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, nullable=True)  # ID пользователя или оператора
    knowledge_base_id = Column(Integer, ForeignKey('knowledge_base.kb_id'), nullable=True)
    is_helpful = Column(Boolean, nullable=True)  # Оценка полезности от пользователя
    created_at = Column(DateTime, server_default=func.now())
    
    # Связи
    ticket = relationship('SupportTicket', back_populates='messages')
    session = relationship('SupportSession', back_populates='messages')
    knowledge_base = relationship('KnowledgeBase', back_populates='messages')


class SupportSession(Base):
    """Сессия чата поддержки"""
    __tablename__ = 'support_sessions'
    
    session_id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey('support_tickets.ticket_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('auth_users.auth_user_id'), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    questions_count = Column(Integer, default=0)  # Количество вопросов пользователя
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    escalated_to_operator = Column(Boolean, default=False)
    satisfaction_rating = Column(Integer, nullable=True)  # Оценка от 1 до 5
    
    # Связи
    ticket = relationship('SupportTicket', back_populates='session')
    user = relationship('AuthUsers', back_populates='support_sessions')
    messages = relationship('SupportMessage', back_populates='session')


class KnowledgeBase(Base):
    """База знаний с популярными вопросами и ответами"""
    __tablename__ = 'knowledge_base'
    
    kb_id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)  # Категория вопроса
    question = Column(Text, nullable=False)  # Популярный вопрос
    answer = Column(Text, nullable=False)  # Краткий ответ
    keywords = Column(Text, nullable=True)  # Ключевые слова для поиска
    faq_url = Column(String(255), nullable=True)  # Ссылка на подробную FAQ страницу
    usage_count = Column(Integer, default=0)  # Количество использований
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Связи
    messages = relationship('SupportMessage', back_populates='knowledge_base') 