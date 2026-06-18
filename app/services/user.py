"""
CRUD сервис для пользователей.

Универсальные операции — можно копировать для любой другой модели:
  1. Скопируй файл
  2. Замени User на свою модель
  3. Замени UserCreate/UserUpdate на свои схемы
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    """Создать пользователя."""
    user = User(**data.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Получить пользователя по ID."""
    return await session.get(User, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Получить пользователя по email."""
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()



async def get_users(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[User], int]:
    """
    Получить список пользователей с пагинацией.
    Возвращает (users, total_count).
    """
    # Total count
    count_result = await session.execute(select(func.count(User.id)))
    total = count_result.scalar_one()

    # Users
    result = await session.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    users = list(result.scalars().all())

    return users, total


async def update_user(
    session: AsyncSession,
    user: User,
    data: UserUpdate,
) -> User:
    """Обновить пользователя (только переданные поля)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user: User) -> None:
    """Удалить пользователя."""
    await session.delete(user)
    await session.commit()
