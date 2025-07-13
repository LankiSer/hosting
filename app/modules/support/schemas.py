from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TicketStatusEnum(str, Enum):
    """Статусы тикетов поддержки"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MessageTypeEnum(str, Enum):
    """Типы сообщений в чате"""
    USER = "user"
    BOT = "bot"
    OPERATOR = "operator"


class SessionStatusEnum(str, Enum):
    """Статусы сессий чата"""
    ACTIVE = "active"
    WAITING_OPERATOR = "waiting_operator"
    WITH_OPERATOR = "with_operator"
    CLOSED = "closed"


class SupportTicketCreate(BaseModel):
    """Схема создания тикета поддержки"""
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=3)


class SupportTicketResponse(BaseModel):
    """Схема ответа тикета поддержки"""
    ticket_id: int
    user_id: int
    title: str
    description: Optional[str]
    status: TicketStatusEnum
    priority: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    assigned_operator_id: Optional[int]
    
    class Config:
        from_attributes = True


class SupportMessageCreate(BaseModel):
    """Схема создания сообщения в чате"""
    content: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[int] = None


class SupportMessageResponse(BaseModel):
    """Схема ответа сообщения в чате"""
    message_id: int
    ticket_id: int
    session_id: Optional[int]
    message_type: MessageTypeEnum
    content: str
    sender_id: Optional[int]
    knowledge_base_id: Optional[int]
    is_helpful: Optional[bool]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatBotResponse(BaseModel):
    """Схема ответа чатбота"""
    message: str
    message_type: MessageTypeEnum
    knowledge_base_id: Optional[int] = None
    is_escalated: bool = False
    suggestions: Optional[List[str]] = None
    session_id: int
    questions_count: int


class PopularQuestion(BaseModel):
    """Схема популярного вопроса"""
    kb_id: int
    category: str
    question: str
    answer: str
    usage_count: int
    
    class Config:
        from_attributes = True


class SupportSessionCreate(BaseModel):
    """Схема создания сессии чата"""
    initial_message: str = Field(..., min_length=1, max_length=2000)


class SupportSessionResponse(BaseModel):
    """Схема ответа сессии чата"""
    session_id: int
    ticket_id: int
    user_id: int
    status: SessionStatusEnum
    questions_count: int
    started_at: datetime
    ended_at: Optional[datetime]
    escalated_to_operator: bool
    satisfaction_rating: Optional[int]
    
    class Config:
        from_attributes = True


class KnowledgeBaseCreate(BaseModel):
    """Схема создания записи в базе знаний"""
    category: str = Field(..., min_length=1, max_length=100)
    question: str = Field(..., min_length=5, max_length=500)
    answer: str = Field(..., min_length=10, max_length=500)  # Краткий ответ
    keywords: Optional[str] = None
    faq_url: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    """Схема ответа записи в базе знаний"""
    kb_id: int
    category: str
    question: str
    answer: str
    keywords: Optional[str]
    faq_url: Optional[str]
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Схема сообщения в чате"""
    message_id: int
    content: str
    message_type: MessageTypeEnum
    created_at: datetime
    is_helpful: Optional[bool] = None
    sender_name: Optional[str] = None


class ChatSession(BaseModel):
    """Схема полной сессии чата"""
    session_id: int
    status: SessionStatusEnum
    questions_count: int
    messages: List[ChatMessage]
    can_escalate: bool
    
    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    """Схема обратной связи"""
    message_id: int
    is_helpful: bool
    comment: Optional[str] = None


class OperatorEscalationRequest(BaseModel):
    """Схема передачи оператору"""
    session_id: int
    reason: str = Field(..., min_length=5, max_length=500)
    priority: int = Field(default=2, ge=1, le=3) 