import json
from aio_pika import Message
from app.core.rabbitmq import get_channel
from typing import Dict, Any


async def send_email_notification(to: str, subject: str, body: str, **kwargs):
    """Отправить email уведомление в очередь"""
    channel = await get_channel()
    message_data = {
        "to": to,
        "subject": subject,
        "body": body,
        "type": "email",
        **kwargs
    }
    
    message = Message(
        json.dumps(message_data).encode(),
        delivery_mode=2  # Persistent message
    )
    
    await channel.default_exchange.publish(
        message,
        routing_key="notifications.email"
    )


async def send_sms_notification(to: str, text: str, **kwargs):
    """Отправить SMS уведомление в очередь"""
    channel = await get_channel()
    message_data = {
        "to": to,
        "text": text,
        "type": "sms",
        **kwargs
    }
    
    message = Message(
        json.dumps(message_data).encode(),
        delivery_mode=2  # Persistent message
    )
    
    await channel.default_exchange.publish(
        message,
        routing_key="notifications.sms"
    )


async def send_hosting_task(task_type: str, task_data: Dict[str, Any]):
    """Отправить задачу хостинга в очередь"""
    channel = await get_channel()
    message_data = {
        "task_type": task_type,
        "task_data": task_data,
        "type": "hosting_task"
    }
    
    message = Message(
        json.dumps(message_data).encode(),
        delivery_mode=2  # Persistent message
    )
    
    await channel.default_exchange.publish(
        message,
        routing_key="hosting.tasks"
    ) 