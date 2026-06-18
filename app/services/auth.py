"""
Сервис аутентификации — JWT токены + хэширование паролей.

Использование:
    from app.services.auth import create_access_token, verify_password

    token = create_access_token(user_id="...")
    is_valid = verify_password("plain", "hashed")
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


# ─── Пароли ───────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Хэширование пароля bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ─── JWT Токены ───────────────────────────────────────────


def create_access_token(user_id: str, extra_data: dict | None = None) -> str:
    """Создать access JWT токен."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    if extra_data:
        payload.update(extra_data)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Создать refresh JWT токен."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(user_id: str) -> dict:
    """Создать пару access + refresh."""
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


def decode_token(token: str) -> dict | None:
    """
    Декодировать и валидировать JWT токен.
    Возвращает payload или None если токен невалидный.
    """
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None


def verify_access_token(token: str) -> dict | None:
    """Проверить access токен — вернуть payload или None."""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def verify_refresh_token(token: str) -> dict | None:
    """Проверить refresh токен — вернуть payload или None."""
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None