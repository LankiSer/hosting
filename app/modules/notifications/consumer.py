import json
import asyncio
from aio_pika import IncomingMessage
from app.core.rabbitmq import get_channel
from typing import Dict, Any
import logging
from app.core.db import async_session_maker
from app.modules.notifications.models import Notification
import bleach


logger = logging.getLogger(__name__)


async def process_email_notification(message_data: Dict[str, Any]):
    """Обработка email уведомления и сохранение в БД"""
    try:
        to = message_data.get("to")
        subject = message_data.get("subject")
        body = message_data.get("body")
        user_id = message_data.get("user_id")
        
        # Здесь должна быть реальная отправка email
        # Например, через SMTP или внешний сервис
        logger.info(f"Отправка email на {to} с темой '{subject}'")
        
        # Симуляция отправки
        await asyncio.sleep(0.1)
        
        logger.info(f"Email успешно отправлен на {to}")
        
        # Сохраняем уведомление в БД
        async with async_session_maker() as session:
            notification = Notification(
                user_id=user_id,
                type="email",
                title=bleach.clean(subject, tags=[], strip=True),
                message=bleach.clean(body, tags=[], strip=True),
                is_read=False
            )
            session.add(notification)
            await session.commit()
        
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {e}")
        raise


async def process_sms_notification(message_data: Dict[str, Any]):
    """Обработка SMS уведомления и сохранение в БД"""
    try:
        to = message_data.get("to")
        text = message_data.get("text")
        user_id = message_data.get("user_id")
        
        # Здесь должна быть реальная отправка SMS
        # Например, через SMS-провайдера
        logger.info(f"Отправка SMS на {to} с текстом '{text}'")
        
        # Симуляция отправки
        await asyncio.sleep(0.1)
        
        logger.info(f"SMS успешно отправлено на {to}")
        
        # Сохраняем уведомление в БД
        async with async_session_maker() as session:
            notification = Notification(
                user_id=user_id,
                type="sms",
                title="SMS",
                message=bleach.clean(text, tags=[], strip=True),
                is_read=False
            )
            session.add(notification)
            await session.commit()
        
    except Exception as e:
        logger.error(f"Ошибка при отправке SMS: {e}")
        raise


async def process_hosting_task(message_data: Dict[str, Any]):
    """Обработка задач хостинга"""
    try:
        task_type = message_data.get("task_type")
        task_data = message_data.get("task_data")
        
        logger.info(f"Обработка задачи хостинга: {task_type}")
        
        # Здесь должна быть реальная обработка задач
        # Например, создание/удаление виртуальных хостов
        await asyncio.sleep(0.1)
        
        logger.info(f"Задача хостинга '{task_type}' успешно выполнена")
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении задачи хостинга: {e}")
        raise


async def consume_notifications():
    """Основной consumer для обработки уведомлений"""
    channel = await get_channel()
    
    # Настройка очередей
    email_queue = await channel.declare_queue("notifications.email", durable=True)
    sms_queue = await channel.declare_queue("notifications.sms", durable=True)
    hosting_queue = await channel.declare_queue("hosting.tasks", durable=True)
    
    # Обработка email уведомлений
    async def handle_email(message: IncomingMessage):
        async with message.process():
            try:
                message_data = json.loads(message.body.decode())
                await process_email_notification(message_data)
            except Exception as e:
                logger.error(f"Ошибка обработки email сообщения: {e}")
                raise
    
    # Обработка SMS уведомлений
    async def handle_sms(message: IncomingMessage):
        async with message.process():
            try:
                message_data = json.loads(message.body.decode())
                await process_sms_notification(message_data)
            except Exception as e:
                logger.error(f"Ошибка обработки SMS сообщения: {e}")
                raise
    
    # Обработка задач хостинга
    async def handle_hosting(message: IncomingMessage):
        async with message.process():
            try:
                message_data = json.loads(message.body.decode())
                await process_hosting_task(message_data)
            except Exception as e:
                logger.error(f"Ошибка обработки задачи хостинга: {e}")
                raise
    
    # Подписка на очереди
    await email_queue.consume(handle_email)
    await sms_queue.consume(handle_sms)
    await hosting_queue.consume(handle_hosting)
    
    logger.info("Consumer запущен и ожидает сообщения...")
    
    # Бесконечный цикл для поддержания работы consumer
    try:
        await asyncio.Future()  # Ожидание бесконечно
    except KeyboardInterrupt:
        logger.info("Consumer остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка в consumer: {e}")
        raise 