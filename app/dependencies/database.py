"""
Dependency: получение сессии БД.

Использование в роутере:
    @router.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        ...
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Получить async сессию БД — автоматически закрывается."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
