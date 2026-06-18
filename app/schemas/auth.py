"""Pydantic схемы для аутентификации."""


from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Запрос на регистрацию."""
    email: EmailStr
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    """Запрос на вход."""
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    """Пара JWT токенов."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Данные из JWT токена."""
    sub: str  # user_id as string
    exp: int
    type: str  # "access" или "refresh"


class RefreshRequest(BaseModel):
    """Запрос на обновление access токена."""
    refresh_token: str


