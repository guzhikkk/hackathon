"""Тесты API аутентификации — register, login, refresh."""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.auth import create_access_token, create_refresh_token, hash_password


# ─── Register ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(unauth_client):
    """Успешная регистрация — возвращает пару токенов."""
    fake_user = SimpleNamespace(id=uuid.uuid4())

    with (
        patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=None),
        patch("app.api.auth.create_user", new_callable=AsyncMock, return_value=fake_user),
    ):
        response = await unauth_client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "password123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_with_name(unauth_client):
    """Регистрация с именем."""
    fake_user = SimpleNamespace(id=uuid.uuid4())

    with (
        patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=None),
        patch("app.api.auth.create_user", new_callable=AsyncMock, return_value=fake_user),
    ):
        response = await unauth_client.post(
            "/api/auth/register",
            json={
                "email": "new@example.com",
                "password": "pass",
                "full_name": "John Doe",
            },
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_register_duplicate_email(unauth_client):
    """Регистрация с уже занятым email → 409."""
    existing = SimpleNamespace(id=uuid.uuid4(), email="taken@example.com")

    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=existing):
        response = await unauth_client.post(
            "/api/auth/register",
            json={"email": "taken@example.com", "password": "pass"},
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_invalid_email(unauth_client):
    """Невалидный email → 422."""
    response = await unauth_client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "pass"},
    )
    assert response.status_code == 422


# ─── Login ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(unauth_client):
    """Успешный логин — возвращает токены."""
    fake_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
    )

    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=fake_user):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_email(unauth_client):
    """Несуществующий email → 401."""
    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=None):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "pass"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(unauth_client):
    """Неправильный пароль → 401."""
    fake_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("correct_password"),
        is_active=True,
    )

    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=fake_user):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrong_password"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(unauth_client):
    """Неактивный аккаунт → 403."""
    fake_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("password123"),
        is_active=False,
    )

    with patch("app.api.auth.get_user_by_email", new_callable=AsyncMock, return_value=fake_user):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

    assert response.status_code == 403


# ─── Refresh ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_success(unauth_client):
    """Обновление токена по валидному refresh."""
    refresh = create_refresh_token("user-123")

    response = await unauth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(unauth_client):
    """Невалидный refresh токен → 401."""
    response = await unauth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token(unauth_client):
    """Нельзя обновить по access токену → 401."""
    access = create_access_token("user-123")

    response = await unauth_client.post(
        "/api/auth/refresh",
        json={"refresh_token": access},
    )
    assert response.status_code == 401
