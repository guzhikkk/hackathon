import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.services.auth import hash_password

@pytest.fixture
def fake_user_id():
    return uuid.UUID("12345678-1234-5678-1234-567812345678")

@pytest.fixture
def fake_user(fake_user_id):
    return SimpleNamespace(
        id=fake_user_id,
        email="test@example.com",
        hashed_password=hash_password("password123"),
        user_data=SimpleNamespace(
            full_name="Test User",
            avatar_url=None,
        ),
        is_active=True,
        is_admin=False,
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0, 0),
    )

@pytest.fixture
def fake_admin(fake_user_id):
    return SimpleNamespace(
        id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        email="admin@example.com",
        hashed_password=hash_password("admin123"),
        user_data=SimpleNamespace(
            full_name="Admin User",
            avatar_url=None,
        ),
        is_active=True,
        is_admin=True,
        created_at=datetime(2024, 1, 1, 0, 0, 0),
        updated_at=datetime(2024, 1, 1, 0, 0, 0),
    )

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest_asyncio.fixture
async def client(fake_user, mock_db):
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
async def admin_client(fake_admin, mock_db):
    from app.dependencies.auth import get_current_user
    from app.dependencies.database import get_db
    from app.main import app

    async def override_get_db():
        yield mock_db

    async def override_get_current_user():
        return fake_admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def unauth_client(mock_db):
    from app.dependencies.database import get_db
    from app.main import app

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
