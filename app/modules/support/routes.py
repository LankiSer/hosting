from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from app.core.db import get_db
from app.modules.auth.routes import get_current_user
from app.modules.auth.models import AuthUsers
from app.modules.support.models import (
    SupportTicket, SupportSession, SupportMessage, KnowledgeBase,
    TicketStatus, SessionStatus, MessageType
)
from app.modules.support.schemas import (
    SupportTicketCreate, SupportTicketResponse, 
    SupportSessionCreate, SupportSessionResponse,
    SupportMessageCreate, SupportMessageResponse,
    ChatBotResponse, PopularQuestion, ChatSession, ChatMessage,
    FeedbackRequest, OperatorEscalationRequest, 
    MessageTypeEnum, SessionStatusEnum
)
from app.modules.support.gigachat_service import gigachat_service
from app.modules.support.init_knowledge_base import initialize_knowledge_base
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/support/init-knowledge-base")
async def init_knowledge_base(
    db: AsyncSession = Depends(get_db),
    current_user: AuthUsers = Depends(get_current_user)
):
    """Инициализация базы знаний (только для администраторов)"""
    # В реальной системе здесь должна быть проверка прав администратора
    await initialize_knowledge_base(db)
    await gigachat_service.load_knowledge_base(db)
    return {"message": "База знаний успешно инициализирована"}

@router.get("/support/popular-questions", response_model=List[PopularQuestion])
async def get_popular_questions(
    db: AsyncSession = Depends(get_db),
    limit: int = 10
):
    """Получение популярных вопросов"""
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.is_active == True)
        .order_by(desc(KnowledgeBase.usage_count))
        .limit(limit)
    )
    questions = result.scalars().all()
    return questions

@router.post("/support/start-session", response_model=SupportSessionResponse)
async def start_support_session(
    session_data: SupportSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUsers = Depends(get_current_user)
):
    """Начало сессии поддержки"""
    try:
        # Создаем тикет
        ticket = SupportTicket(
            user_id=current_user.auth_user_id,
            title=f"Поддержка: {session_data.initial_message[:50]}...",
            description=session_data.initial_message,
            status=TicketStatus.OPEN,
            priority=1
        )
        db.add(ticket)
        await db.flush()
        
        # Создаем сессию
        session = SupportSession(
            ticket_id=ticket.ticket_id,
            user_id=current_user.auth_user_id,
            status=SessionStatus.ACTIVE,
            questions_count=0
        )
        db.add(session)
        await db.flush()
        
        # Сохраняем первое сообщение пользователя
        user_message = SupportMessage(
            ticket_id=ticket.ticket_id,
            session_id=session.session_id,
            message_type=MessageType.USER,
            content=session_data.initial_message,
            sender_id=current_user.auth_user_id
        )
        db.add(user_message)
        
        await db.commit()
        
        # Загружаем базу знаний если нужно
        if not gigachat_service.knowledge_base_data:
            await gigachat_service.load_knowledge_base(db)
        
        return SupportSessionResponse(
            session_id=session.session_id,
            ticket_id=ticket.ticket_id,
            user_id=current_user.auth_user_id,
            status=SessionStatusEnum.ACTIVE,
            questions_count=0,
            started_at=session.started_at,
            ended_at=None,
            escalated_to_operator=False,
            satisfaction_rating=None
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при создании сессии поддержки: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось создать сессию поддержки"
        )

@router.post("/support/send-message", response_model=ChatBotResponse)
async def send_message(
    message_data: SupportMessageCreate,
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUsers = Depends(get_current_user)
):
    """Отправка сообщения в чат поддержки"""
    try:
        # Проверяем существование сессии
        session_result = await db.execute(
            select(SupportSession)
            .where(
                SupportSession.session_id == session_id,
                SupportSession.user_id == current_user.auth_user_id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия не найдена"
            )
        
        if session.status == SessionStatus.CLOSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Сессия закрыта"
            )
        
        # Загружаем базу знаний если нужно
        if not gigachat_service.knowledge_base_data:
            await gigachat_service.load_knowledge_base(db)
        
        # Обрабатываем сообщение через GigaChat сервис
        bot_response = await gigachat_service.process_user_message(
            db, session_id, message_data.content
        )
        
        return bot_response
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при отправке сообщения: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обработать сообщение"
        )

@router.get("/support/session/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUsers = Depends(get_current_user)
):
    """Получение полной сессии чата"""
    try:
        # Получаем сессию
        session_result = await db.execute(
            select(SupportSession)
            .where(
                SupportSession.session_id == session_id,
                SupportSession.user_id == current_user.auth_user_id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия не найдена"
            )
        
        # Получаем сообщения
        messages_result = await db.execute(
            select(SupportMessage)
            .where(SupportMessage.session_id == session_id)
            .order_by(SupportMessage.created_at)
        )
        messages = messages_result.scalars().all()
        
        # Формируем ответ
        chat_messages = []
        for msg in messages:
            sender_name = None
            if msg.message_type == MessageType.USER:
                sender_name = current_user.username
            elif msg.message_type == MessageType.BOT:
                sender_name = "Помощник"
            
            chat_messages.append(ChatMessage(
                message_id=msg.message_id,
                content=msg.content,
                message_type=MessageTypeEnum(msg.message_type.value),
                created_at=msg.created_at,
                is_helpful=msg.is_helpful,
                sender_name=sender_name
            ))
        
        return ChatSession(
            session_id=session.session_id,
            status=SessionStatusEnum(session.status.value),
            questions_count=session.questions_count,
            messages=chat_messages,
            can_escalate=session.questions_count >= 3 and not session.escalated_to_operator
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении сессии: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить сессию"
        )

@router.post("/support/feedback")
async def provide_feedback(
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUsers = Depends(get_current_user)
):
    """Оценка полезности ответа"""
    try:
        # Находим сообщение и обновляем оценку
        message_result = await db.execute(
            select(SupportMessage)
            .where(SupportMessage.message_id == feedback.message_id)
        )
        message = message_result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сообщение не найдено"
            )
        
        message.is_helpful = feedback.is_helpful
        await db.commit()
        
        return {"message": "Спасибо за обратную связь!"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при обработке обратной связи: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось обработать обратную связь"
        )

@router.post("/support/escalate")
async def escalate_to_operator(
    escalation: OperatorEscalationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AuthUsers = Depends(get_current_user)
):
    """Передача оператору"""
    try:
        # Находим сессию
        session_result = await db.execute(
            select(SupportSession)
            .where(
                SupportSession.session_id == escalation.session_id,
                SupportSession.user_id == current_user.auth_user_id
            )
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сессия не найдена"
            )
        
        # Обновляем сессию
        session.escalated_to_operator = True
        session.status = SessionStatus.WAITING_OPERATOR
        
        # Обновляем тикет
        ticket_result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.ticket_id == session.ticket_id)
        )
        ticket = ticket_result.scalar_one_or_none()
        
        if ticket:
            ticket.status = TicketStatus.IN_PROGRESS
            ticket.priority = escalation.priority
            ticket.description += f"\n\nПричина передачи оператору: {escalation.reason}"
        
        # Добавляем системное сообщение
        system_message = SupportMessage(
            ticket_id=session.ticket_id,
            session_id=session.session_id,
            message_type=MessageType.BOT,
            content="Ваш запрос передан оператору. Ожидайте, пожалуйста.",
            sender_id=None
        )
        db.add(system_message)
        
        await db.commit()
        
        return {"message": "Запрос передан оператору. Ожидайте подключения."}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при передаче оператору: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось передать запрос оператору"
        )

@router.get("/support/my-tickets", response_model=List[SupportTicketResponse])
async def get_user_tickets(
    db: AsyncSession = Depends(get_db),
    current_user: AuthUsers = Depends(get_current_user),
    limit: int = 10
):
    """Получение тикетов пользователя"""
    try:
        result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == current_user.auth_user_id)
            .order_by(desc(SupportTicket.created_at))
            .limit(limit)
        )
        tickets = result.scalars().all()
        return tickets
        
    except Exception as e:
        logger.error(f"Ошибка при получении тикетов: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить тикеты"
        ) 