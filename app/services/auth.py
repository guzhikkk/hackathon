"""
Сервис аутентификации — JWT токены + хэширование паролей.

Использование:
    from app.services.auth import create_access_token, verify_password

    token = create_access_token(user_id="...")
    is_valid = verify_password("plain", "hashed")
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Bcrypt контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Пароли ───────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Хэширование пароля bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля."""
    return pwd_context.verify(plain_password, hashed_password)


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
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
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
