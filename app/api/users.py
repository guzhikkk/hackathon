"""
Роутер пользователей — CRUD.

Эндпоинты:
  GET    /api/users       — список пользователей (с пагинацией)
  GET    /api/users/me    — текущий пользователь (алиас /auth/me)
  GET    /api/users/{id}  — по ID
  PATCH  /api/users/me    — обновить свой профиль
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import CurrentUser
from app.dependencies.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserRead, UserUpdate
from app.services.user import get_user_by_id, get_users, update_user

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_current_user_profile(user: CurrentUser):
    """Получить профиль текущего пользователя."""
    return user


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    data: UserUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Обновить профиль текущего пользователя."""
    updated = await update_user(db, user, data)
    return updated


@router.get("", response_model=PaginatedResponse[UserRead])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Размер страницы"),
):
    """Список пользователей с пагинацией."""
    offset = (page - 1) * size
    users, total = await get_users(db, offset=offset, limit=size)
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        size=size,
    )


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Получить пользователя по ID."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
