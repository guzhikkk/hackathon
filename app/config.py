"""
Конфигурация приложения.

Все настройки читаются из .env файла через pydantic-settings.
На хакатоне просто скопируй .env.example -> .env и поправь нужные значения.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Главный конфиг — все переменные из .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "HackathonApp"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://hackathon:hackathon@localhost:5432/hackathon"

    # --- JWT ---
    JWT_SECRET_KEY: str = "super-secret-change-me-on-hackathon"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- S3 / MinIO ---
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "uploads"
    S3_REGION: str = "us-east-1"

    # --- CORS ---
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    """Синглтон настроек — вызывай из любого места."""
    return Settings()
