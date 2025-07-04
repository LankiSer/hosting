import asyncio
import logging
from app.core.rabbitmq import init_rabbitmq, close_rabbitmq
from app.modules.notifications.consumer import consume_notifications


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция воркера"""
    try:
        logger.info("Запуск RabbitMQ воркера...")
        
        # Инициализация RabbitMQ
        await init_rabbitmq()
        logger.info("RabbitMQ подключен успешно")
        
        # Запуск consumer
        await consume_notifications()
        
    except Exception as e:
        logger.error(f"Ошибка в воркере: {e}")
        raise
    finally:
        # Закрытие соединения
        await close_rabbitmq()
        logger.info("RabbitMQ соединение закрыто")


if __name__ == "__main__":
    asyncio.run(main()) 