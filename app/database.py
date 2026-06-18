"""
Подключение к базе данных (async SQLAlchemy).

Использование:
    from app.database import async_session_maker

    async with async_session_maker() as session:
        result = await session.execute(select(User))
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

# Engine — пул соединений к PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Проверка подключения к БД при старте."""
    async with engine.begin() as conn:
        # Простая проверка что БД доступна
        await conn.execute(text("SELECT 1"))


async def dispose_db() -> None:
    """Закрытие пула соединений при остановке."""
    await engine.dispose()
