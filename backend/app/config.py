from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://hackathon:hackathon@localhost:5432/hackathon"
    JWT_SECRET_KEY: str = "super-secret-change-me-on-hackathon"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "uploads"
    S3_REGION: str = "us-east-1"
    GIGACHAT_CREDENTIALS: str | None = None
    AI_PROVIDER: str = "gigachat"
    LOCAL_AI_BASE_URL: str = "http://localhost:11434/v1"
    LOCAL_AI_API_KEY: str = "ollama"
    RESEND_API_KEY: str = ""

@lru_cache
def get_settings() -> Settings:
    return Settings()
