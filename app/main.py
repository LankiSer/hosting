from fastapi import FastAPI, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.db import init_db
from app.core.rabbitmq import init_rabbitmq, close_rabbitmq
from app.modules.notifications.producer import send_email_notification
from app.core import models  # Импорт моделей для создания таблиц
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.middleware.security import SecurityMiddleware, InputSanitizationMiddleware

# Импорт роутов
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.domains.routes import router as domains_router
from app.modules.hosting.routes import router as hosting_router
from app.modules.plans.routes import router as plans_router
from app.modules.billing.routes import router as billing_router
from app.modules.notifications.routes import router as notifications_router
from app.modules.support.routes import router as support_router

import logging

# Настройка логирования
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events для FastAPI"""
    try:
        # Инициализация при запуске
        logger.info("Инициализация приложения...")
        
        # Инициализация БД
        await init_db()
        logger.info("База данных инициализирована")
        
        # Инициализация RabbitMQ
        await init_rabbitmq()
        logger.info("RabbitMQ подключен")
        
        yield
        
    except Exception as e:
        logger.error(f"Ошибка при инициализации: {e}")
        raise
    finally:
        # Закрытие соединений при остановке
        await close_rabbitmq()
        logger.info("Соединения закрыты")


# Создание FastAPI приложения
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan
)

# Инициализация Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Добавляем middleware безопасности
app.add_middleware(SecurityMiddleware)
app.add_middleware(InputSanitizationMiddleware)

# Настройка CORS с улучшенной безопасностью
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",  # Альтернативный порт
        "http://127.0.0.1:3000",
        # В продакшене добавить только нужные домены
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["X-Total-Count"],
    max_age=86400,  # 24 часа кеширования preflight запросов
)


# Подключение роутов
app.include_router(auth_router, tags=["Авторизация"])
app.include_router(users_router, tags=["Пользователи"])
app.include_router(domains_router, tags=["Домены"])
app.include_router(hosting_router, tags=["Хостинг"])
app.include_router(plans_router, tags=["Тарифы"])
app.include_router(billing_router, tags=["Биллинг"])
app.include_router(notifications_router, tags=["Уведомления"])
app.include_router(support_router, tags=["Поддержка"])


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Shared Hosting API запущен!", 
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy", 
        "database": "connected", 
        "rabbitmq": "connected",
        "api_version": settings.api_version
    }


@app.post("/test-email")
async def test_email_notification(to: str, subject: str = "Тестовое уведомление"):
    """Тестовый endpoint для отправки email уведомления"""
    try:
        await send_email_notification(
            to=to,
            subject=subject,
            body="Это тестовое уведомление от Shared Hosting API"
        )
        return {"message": f"Email уведомление отправлено на {to}"}
    except Exception as e:
        logger.error(f"Ошибка при отправке email: {e}")
        return {"error": "Ошибка при отправке email"} 