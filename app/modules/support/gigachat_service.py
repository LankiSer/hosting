import asyncio
import httpx
import json
import logging
from typing import Optional, List, Dict, Any
import re
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.modules.support.models import KnowledgeBase, SupportSession, SupportMessage, MessageType
from app.modules.support.schemas import ChatBotResponse, MessageTypeEnum
from app.core.config import settings

logger = logging.getLogger(__name__)

class GigaChatService:
    """Сервис для работы с GigaChat API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'gigachat_api_key', 'your_gigachat_api_key_here')
        self.oauth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.knowledge_base_data = []
        self.access_token = None
        self.token_expires_at = None
        
    async def get_access_token(self) -> Optional[str]:
        """Получение токена доступа для GigaChat API"""
        import datetime
        import uuid
        
        # Проверяем, есть ли действующий токен
        if self.access_token and self.token_expires_at:
            if datetime.datetime.now() < self.token_expires_at:
                return self.access_token
        
        try:
            async with httpx.AsyncClient(verify=False) as client:  # verify=False для обхода SSL проблем
                response = await client.post(
                    self.oauth_url,
                    headers={
                        "Authorization": f"Basic {self.api_key}",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                        "RqUID": str(uuid.uuid4())
                    },
                    data={
                        "scope": "GIGACHAT_API_PERS"
                    }
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get('access_token')
                    
                    # Токен действует 30 минут
                    self.token_expires_at = datetime.datetime.now() + datetime.timedelta(minutes=25)  # С запасом
                    
                    logger.info("GigaChat токен успешно получен")
                    return self.access_token
                else:
                    logger.error(f"Ошибка получения токена: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка при получении токена: {str(e)}")
            return None
    
    async def load_knowledge_base(self, db: AsyncSession):
        """Загрузка базы знаний для векторизации"""
        try:
            result = await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.is_active == True)
            )
            knowledge_items = result.scalars().all()
            
            self.knowledge_base_data = [
                {
                    'id': kb.kb_id,
                    'category': kb.category,
                    'question': kb.question,
                    'answer': kb.answer,
                    'keywords': kb.keywords or '',
                    'faq_url': kb.faq_url,
                    'usage_count': kb.usage_count
                }
                for kb in knowledge_items
            ]
            
            if self.knowledge_base_data:
                logger.info(f"Загружена база знаний: {len(self.knowledge_base_data)} записей")
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке базы знаний: {str(e)}")
    
    def find_best_answer(self, user_message: str, min_score: int = 2) -> Optional[Dict[str, Any]]:
        """Поиск наиболее подходящего ответа из базы знаний"""
        if not self.knowledge_base_data:
            return None
            
        try:
            user_message_lower = user_message.lower()
            best_match = None
            best_score = 0
            
            for kb_item in self.knowledge_base_data:
                score = 0
                
                # Очки за совпадения в вопросе
                question_words = kb_item['question'].lower().split()
                for word in question_words:
                    if len(word) > 3 and word in user_message_lower:
                        score += 3
                
                # Очки за совпадения в ключевых словах
                if kb_item['keywords']:
                    keywords = [kw.strip().lower() for kw in kb_item['keywords'].split(',')]
                    for keyword in keywords:
                        if len(keyword) > 2 and keyword in user_message_lower:
                            score += 2
                
                # Очки за совпадения в категории
                if kb_item['category'].lower() in user_message_lower:
                    score += 1
                
                # Проверяем точные фразы (регистронезависимо)
                question_lower = kb_item['question'].lower()
                if any(phrase in user_message_lower for phrase in question_lower.split() if len(phrase) > 4):
                    score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = kb_item
            
            if best_match and best_score >= min_score:
                answer = best_match['answer']
                
                # Добавляем FAQ ссылку если есть
                if best_match.get('faq_url'):
                    answer += f" 🔗 Подробнее: {best_match['faq_url']}"
                
                return {
                    'knowledge_base_id': best_match['id'],
                    'answer': answer,
                    'question': best_match['question'],
                    'score': best_score,
                    'category': best_match['category'],
                    'faq_url': best_match.get('faq_url')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при поиске ответа: {str(e)}")
            return None
    
    async def ask_gigachat(self, message: str, context: str = "") -> Optional[str]:
        """Запрос к GigaChat API"""
        try:
            access_token = await self.get_access_token()
            if not access_token:
                logger.error("Не удалось получить токен для GigaChat")
                return None
                
            prompt = f"""Ты - помощник службы поддержки хостинг-провайдера.
{context}

Пользователь спрашивает: {message}

Ответь кратко (максимум 50 слов) и направь на подробную статью в FAQ если она есть.
Если вопрос не связан с хостингом, попроси перефразировать."""
            
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "model": "GigaChat",
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 150,
                        "temperature": 0.5
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('choices') and len(result['choices']) > 0:
                        return result['choices'][0]['message']['content']
                    else:
                        logger.error("Пустой ответ от GigaChat")
                        return None
                else:
                    logger.error(f"Ошибка GigaChat API: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Ошибка при запросе к GigaChat: {str(e)}")
            return None
    
    async def process_user_message(
        self, 
        db: AsyncSession, 
        session_id: int, 
        user_message: str
    ) -> ChatBotResponse:
        """Обработка сообщения пользователя"""
        try:
            # Получаем сессию
            session_result = await db.execute(
                select(SupportSession).where(SupportSession.session_id == session_id)
            )
            session = session_result.scalar_one_or_none()
            
            if not session:
                raise ValueError("Сессия не найдена")
            
            # Увеличиваем счетчик вопросов
            session.questions_count += 1
            
            # Сохраняем сообщение пользователя
            user_msg = SupportMessage(
                ticket_id=session.ticket_id,
                session_id=session_id,
                message_type=MessageType.USER,
                content=user_message,
                sender_id=session.user_id
            )
            db.add(user_msg)
            await db.flush()
            
            # Ищем ответ в базе знаний
            best_answer = self.find_best_answer(user_message)
            
            bot_response = None
            is_escalated = False
            knowledge_base_id = None
            
            if best_answer and best_answer['score'] >= 3:
                # Используем ответ из базы знаний
                bot_response = best_answer['answer']
                knowledge_base_id = best_answer['knowledge_base_id']
                
                # Увеличиваем счетчик использования
                await db.execute(
                    update(KnowledgeBase)
                    .where(KnowledgeBase.kb_id == knowledge_base_id)
                    .values(usage_count=KnowledgeBase.usage_count + 1)
                )
                
            elif session.questions_count >= 5:
                # Передаем оператору после 5 вопросов
                bot_response = "Я передаю вас оператору для более детальной помощи. Пожалуйста, подождите."
                is_escalated = True
                session.escalated_to_operator = True
                session.status = "waiting_operator"
                
            else:
                # Запрашиваем GigaChat
                context = "Пользователь задает вопрос по хостингу. Предыдущих вопросов: " + str(session.questions_count)
                gigachat_response = await self.ask_gigachat(user_message, context)
                
                if gigachat_response:
                    bot_response = gigachat_response
                else:
                    bot_response = "Извините, не могу обработать ваш запрос. Попробуйте перефразировать вопрос."
            
            # Сохраняем ответ бота
            if bot_response:
                bot_msg = SupportMessage(
                    ticket_id=session.ticket_id,
                    session_id=session_id,
                    message_type=MessageType.BOT,
                    content=bot_response,
                    knowledge_base_id=knowledge_base_id
                )
                db.add(bot_msg)
            
            await db.commit()
            
            # Предложения для продолжения диалога
            suggestions = []
            if not is_escalated and session.questions_count < 4:
                suggestions = [
                    "Это помогло решить проблему?",
                    "Нужна дополнительная помощь?",
                    "Есть другие вопросы?"
                ]
            
            return ChatBotResponse(
                message=bot_response,
                message_type=MessageTypeEnum.BOT,
                knowledge_base_id=knowledge_base_id,
                is_escalated=is_escalated,
                suggestions=suggestions,
                session_id=session_id,
                questions_count=session.questions_count
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {str(e)}")
            await db.rollback()
            raise

# Глобальный экземпляр сервиса
gigachat_service = GigaChatService() 