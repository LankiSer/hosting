import aio_pika
from aio_pika import Connection, Channel
from app.core.config import settings
from typing import Optional


connection: Optional[Connection] = None
channel: Optional[Channel] = None


async def init_rabbitmq():
    """Инициализация подключения к RabbitMQ"""
    global connection, channel
    
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    
    # Создание основных очередей
    await channel.declare_queue("notifications.email", durable=True)
    await channel.declare_queue("notifications.sms", durable=True)
    await channel.declare_queue("hosting.tasks", durable=True)
    

async def close_rabbitmq():
    """Закрытие подключения к RabbitMQ"""
    global connection, channel
    
    if channel:
        await channel.close()
    if connection:
        await connection.close()


async def get_channel() -> Channel:
    """Получение канала RabbitMQ"""
    global channel
    if channel is None or channel.is_closed:
        await init_rabbitmq()
    return channel 