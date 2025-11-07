import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.logging_config import setup_logging
from app.modules.auth.routes import router as auth_router
from app.modules.domains.routes import router as domains_router
from app.modules.hosting.routes import router as hosting_router
from app.modules.users.routes import router as users_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run lightweight startup tasks."""

    logger.info("Running pending database migrations")
    await init_db()
    logger.info("Migrations completed")

    yield


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["X-Total-Count"],
    max_age=86400,
)


app.include_router(auth_router, tags=["Авторизация"])
app.include_router(users_router, tags=["Пользователи"])
app.include_router(domains_router, tags=["Домены"])
app.include_router(hosting_router, tags=["Хостинг"])


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Shared Hosting API запущен!",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "api_version": settings.api_version,
    }