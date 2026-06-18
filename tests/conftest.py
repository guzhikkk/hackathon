"""
Общие фикстуры для всех тестов.

Главные фикстуры:
  - fake_user      — тестовый пользователь (SimpleNamespace)
  - mock_db        — замоканная async сессия БД
  - client         — HTTP-клиент С авторизацией (для защищённых эндпоинтов)
  - unauth_client  — HTTP-клиент БЕЗ авторизации (для register/login/refresh)
"""

import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.services.auth import hash_password


# ─── Данные ──────────────────────────────────────────────


@pytest.fixture
def fake_user_id():
    """Фиксированный UUID для тестового пользователя."""
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def fake_user(fake_user_id):
    """Тестовый пользователь (имитирует ORM-объект User)."""
    return SimpleNamespace(
        id=fake_user_id,
        email="test@example.com",
        hashed_password=hash_password("password123"),
        full_name="Test User",
        avatar_url=None,
        is_active=True,
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0, 0),
    )


@pytest.fixture
def mock_db():
    """Mock async DB session."""
    return AsyncMock()


# ─── HTTP-клиенты ───────────────────────────────────────


@pytest_asyncio.fixture
async def client(fake_user, mock_db):
    """HTTP-клиент С авторизацией — для защищённых эндпоинтов."""
    from app.dependencies.auth import get_current_user
    from app.dependencies.database import get_db
    from app.main import app

    async def override_get_db():
        yield mock_db

    async def override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def unauth_client(mock_db):
    """HTTP-клиент БЕЗ авторизации — для register/login/refresh."""
    from app.dependencies.database import get_db
    from app.main import app

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
