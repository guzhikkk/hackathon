"""Тесты API пользователей — CRUD эндпоинты."""

import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


# ─── GET /me ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_me(client):
    """Текущий пользователь."""
    response = await client.get("/api/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True


# ─── PATCH /me ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_me(client, fake_user):
    """Обновление имени профиля."""
    updated = SimpleNamespace(
        id=fake_user.id,
        email=fake_user.email,
        full_name="Updated Name",
        avatar_url=None,
        is_active=True,
        created_at=fake_user.created_at,
        updated_at=datetime(2024, 6, 1),
    )

    with patch("app.api.users.update_user", new_callable=AsyncMock, return_value=updated):
        response = await client.patch(
            "/api/users/me",
            json={"full_name": "Updated Name"},
        )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_me_avatar(client, fake_user):
    """Обновление аватара."""
    updated = SimpleNamespace(
        id=fake_user.id,
        email=fake_user.email,
        full_name=fake_user.full_name,
        avatar_url="https://example.com/new-avatar.jpg",
        is_active=True,
        created_at=fake_user.created_at,
        updated_at=datetime(2024, 6, 1),
    )

    with patch("app.api.users.update_user", new_callable=AsyncMock, return_value=updated):
        response = await client.patch(
            "/api/users/me",
            json={"avatar_url": "https://example.com/new-avatar.jpg"},
        )

    assert response.status_code == 200
    assert response.json()["avatar_url"] == "https://example.com/new-avatar.jpg"


# ─── DELETE /me ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_me(client, fake_user):
    """Удаление своего профиля."""
    with patch("app.api.users.delete_user", new_callable=AsyncMock) as mock_delete:
        response = await client.delete("/api/users/me")

    assert response.status_code == 204
    mock_delete.assert_called_once()


# ─── GET /users ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_users(client, fake_user):
    """Список пользователей."""
    with patch("app.api.users.get_users", new_callable=AsyncMock, return_value=([fake_user], 1)):
        response = await client.get("/api/users")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_list_users_pagination(client):
    """Пагинация — page и size передаются."""
    with patch("app.api.users.get_users", new_callable=AsyncMock, return_value=([], 0)):
        response = await client.get("/api/users?page=2&size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["size"] == 10
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_users_empty(client):
    """Пустой список."""
    with patch("app.api.users.get_users", new_callable=AsyncMock, return_value=([], 0)):
        response = await client.get("/api/users")

    assert response.status_code == 200
    assert response.json()["items"] == []


# ─── GET /users/{id} ────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_by_id(client, fake_user):
    """Получить пользователя по ID."""
    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=fake_user):
        response = await client.get(f"/api/users/{fake_user.id}")

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(client):
    """Несуществующий ID → 404."""
    random_id = uuid.uuid4()

    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=None):
        response = await client.get(f"/api/users/{random_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_invalid_id(client):
    """Невалидный UUID → 422."""
    response = await client.get("/api/users/not-a-uuid")
    assert response.status_code == 422
