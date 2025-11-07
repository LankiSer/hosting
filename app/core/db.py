import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


logger = logging.getLogger("app.core.db")


# Создание асинхронного движка БД
engine = create_async_engine(settings.database_url, echo=settings.database_echo)

# Создание асинхронного сеанса
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency для получения сессии БД"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def run_migrations() -> None:
    """Apply raw SQL migrations located in app/migrations/sql."""

    migrations_dir = Path(__file__).resolve().parent.parent / "migrations" / "sql"

    if not migrations_dir.exists():
        logger.info("Migrations directory %s not found, skipping", migrations_dir)
        return

    async with engine.begin() as conn:
        await conn.exec_driver_sql(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """
        )

        result = await conn.execute(text("SELECT version FROM schema_migrations"))
        applied_versions = set(result.scalars().all())

        for migration_file in sorted(migrations_dir.glob("*.sql")):
            prefix, separator, _ = migration_file.name.partition("__")
            migration_id = prefix if separator else migration_file.stem

            if migration_id in applied_versions:
                continue

            sql = migration_file.read_text(encoding="utf-8")
            statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]

            logger.info("Applying migration %s", migration_file.name)

            for statement in statements:
                await conn.exec_driver_sql(statement)

            await conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": migration_id},
            )

            applied_versions.add(migration_id)


async def init_db() -> None:
    """Initialization hook used on startup."""

    await run_migrations()