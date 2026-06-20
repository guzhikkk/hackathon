import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_me(client):
    response = await client.get("/api/users/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["user_data"]["full_name"] == "Test User"
    assert data["is_active"] is True
    assert data["is_admin"] is False

@pytest.mark.asyncio
async def test_update_me(client, fake_user):
    updated = SimpleNamespace(
        id=fake_user.id,
        email=fake_user.email,
        user_data=SimpleNamespace(
            full_name="Updated Name",
            avatar_url=None,
        ),
        is_active=True,
        is_admin=False,
        created_at=fake_user.created_at,
        updated_at=datetime(2024, 6, 1),
    )

    with patch("app.api.users.update_user", new_callable=AsyncMock, return_value=updated):
        response = await client.patch(
            "/api/users/me",
            json={"full_name": "Updated Name"},
        )

    assert response.status_code == 200
    assert response.json()["user_data"]["full_name"] == "Updated Name"

@pytest.mark.asyncio
async def test_update_me_avatar(client, fake_user):
    updated = SimpleNamespace(
        id=fake_user.id,
        email=fake_user.email,
        user_data=SimpleNamespace(
            full_name=fake_user.user_data.full_name,
            avatar_url="https://example.com/new-avatar.jpg",
        ),
        is_active=True,
        is_admin=False,
        created_at=fake_user.created_at,
        updated_at=datetime(2024, 6, 1),
    )

    with patch("app.api.users.update_user", new_callable=AsyncMock, return_value=updated):
        response = await client.patch(
            "/api/users/me",
            json={"avatar_url": "https://example.com/new-avatar.jpg"},
        )

    assert response.status_code == 200
    assert response.json()["user_data"]["avatar_url"] == "https://example.com/new-avatar.jpg"

@pytest.mark.asyncio
async def test_delete_me(client, fake_user):
    with patch("app.api.users.delete_user", new_callable=AsyncMock) as mock_delete:
        response = await client.delete("/api/users/me")

    assert response.status_code == 204
    mock_delete.assert_called_once()

@pytest.mark.asyncio
async def test_list_users_admin(admin_client, fake_user):
    with patch("app.api.users.get_users", new_callable=AsyncMock, return_value=[fake_user]):
        response = await admin_client.get("/api/users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_list_users_forbidden(client):
    response = await client.get("/api/users")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_list_users_empty(admin_client):
    with patch("app.api.users.get_users", new_callable=AsyncMock, return_value=[]):
        response = await admin_client.get("/api/users")

    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_user_by_id_admin(admin_client, fake_user):
    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=fake_user):
        response = await admin_client.get(f"/api/users/{fake_user.id}")

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_user_by_id_forbidden(client, fake_user):
    response = await client.get(f"/api/users/{fake_user.id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_user_not_found(admin_client):
    random_id = uuid.uuid4()

    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=None):
        response = await admin_client.get(f"/api/users/{random_id}")

    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_user_invalid_id(admin_client):
    response = await admin_client.get("/api/users/not-a-uuid")
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_admin_update_user(admin_client, fake_user):
    updated = SimpleNamespace(
        id=fake_user.id,
        email=fake_user.email,
        user_data=SimpleNamespace(
            full_name="Admin Changed",
            avatar_url=None,
        ),
        is_active=True,
        is_admin=False,
        created_at=fake_user.created_at,
        updated_at=datetime(2024, 6, 1),
    )

    with (
        patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=fake_user),
        patch("app.api.users.update_user", new_callable=AsyncMock, return_value=updated),
    ):
        response = await admin_client.patch(
            f"/api/users/{fake_user.id}",
            json={"full_name": "Admin Changed"},
        )

    assert response.status_code == 200
    assert response.json()["user_data"]["full_name"] == "Admin Changed"

@pytest.mark.asyncio
async def test_admin_update_user_forbidden(client, fake_user):
    response = await client.patch(
        f"/api/users/{fake_user.id}",
        json={"full_name": "Hacked"},
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_update_user_not_found(admin_client):
    random_id = uuid.uuid4()
    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=None):
        response = await admin_client.patch(
            f"/api/users/{random_id}",
            json={"full_name": "Nobody"},
        )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_admin_delete_user(admin_client, fake_user):
    with (
        patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=fake_user),
        patch("app.api.users.delete_user", new_callable=AsyncMock),
    ):
        response = await admin_client.delete(f"/api/users/{fake_user.id}")

    assert response.status_code == 204

@pytest.mark.asyncio
async def test_admin_delete_user_forbidden(client, fake_user):
    response = await client.delete(f"/api/users/{fake_user.id}")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_delete_user_not_found(admin_client):
    random_id = uuid.uuid4()
    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=None):
        response = await admin_client.delete(f"/api/users/{random_id}")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_role(admin_client, fake_user, mock_db):
    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=fake_user):
        response = await admin_client.patch(
            f"/api/users/{fake_user.id}/role",
            json={"is_admin": True},
        )

    assert response.status_code == 200
    assert response.json()["is_admin"] is True

@pytest.mark.asyncio
async def test_update_role_forbidden(client, fake_user):
    response = await client.patch(
        f"/api/users/{fake_user.id}/role",
        json={"is_admin": True},
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_role_not_found(admin_client):
    random_id = uuid.uuid4()
    with patch("app.api.users.get_user_by_id", new_callable=AsyncMock, return_value=None):
        response = await admin_client.patch(
            f"/api/users/{random_id}/role",
            json={"is_admin": True},
        )
    assert response.status_code == 404
