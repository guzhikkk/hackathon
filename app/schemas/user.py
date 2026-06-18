"""Pydantic схемы для User."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Создание пользователя (внутреннее, из сервиса)."""
    email: EmailStr
    hashed_password: str
    full_name: str = ""
    avatar_url: str | None = None


class UserRead(BaseModel):
    """Ответ — данные пользователя (публичные)."""
    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Обновление профиля пользователя."""
    full_name: str | None = None
    avatar_url: str | None = None
