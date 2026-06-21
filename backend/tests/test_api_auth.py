import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.services.auth import create_access_token, create_refresh_token, hash_password

@pytest.mark.asyncio
async def test_register_success(unauth_client):
    fake_user = SimpleNamespace(id=uuid.uuid4(), email="test@example.com")

    with (
        patch("app.services.auth.get_user_by_email", return_value=None),
        patch("app.services.auth.create_user", return_value=fake_user, create=True),
    ):
        response = await unauth_client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "password123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_with_name(unauth_client):
    fake_user = SimpleNamespace(id=uuid.uuid4(), email="test@example.com")

    with (
        patch("app.services.auth.get_user_by_email", return_value=None),
        patch("app.services.auth.create_user", return_value=fake_user, create=True),
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
    existing = SimpleNamespace(id=uuid.uuid4(), email="taken@example.com")

    with patch("app.services.auth.get_user_by_email", return_value=existing):
        response = await unauth_client.post(
            "/api/auth/register",
            json={"email": "taken@example.com", "password": "pass"},
        )

    assert response.status_code == 409

@pytest.mark.asyncio
async def test_login_success(unauth_client):
    fake_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
    )

    with patch("app.services.auth.get_user_by_email", return_value=fake_user):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

@pytest.mark.asyncio
async def test_login_wrong_email(unauth_client):
    with patch("app.services.auth.get_user_by_email", return_value=None):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "pass"},
        )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_wrong_password(unauth_client):
    fake_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("correct_password"),
        is_active=True,
    )

    with patch("app.services.auth.get_user_by_email", return_value=fake_user):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrong_password"},
        )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_inactive_user(unauth_client):
    fake_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=hash_password("password123"),
        is_active=False,
    )

    with patch("app.services.auth.get_user_by_email", return_value=fake_user):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_refresh_success(unauth_client):
    fake_id = uuid.uuid4()
    refresh = create_refresh_token(str(fake_id))
    fake_user = SimpleNamespace(
        id=fake_id,
        email="test@example.com",
        is_active=True,
    )

    with patch("app.services.auth.get_user_by_id", return_value=fake_user):
        unauth_client.cookies.set("refresh_token", refresh)
        response = await unauth_client.post("/api/auth/refresh")

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_refresh_invalid_token(unauth_client):
    unauth_client.cookies.set("refresh_token", "invalid-token")
    response = await unauth_client.post("/api/auth/refresh")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_with_access_token(unauth_client):
    access = create_access_token("user-123")
    unauth_client.cookies.set("refresh_token", access)
    response = await unauth_client.post("/api/auth/refresh")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_google_login_redirect(unauth_client):
    with patch("app.api.auth.settings.GOOGLE_CLIENT_ID", "mock_id"):
        response = await unauth_client.get("/api/auth/google/login", follow_redirects=False)
        assert response.status_code == 307
        assert "accounts.google.com/o/oauth2/v2/auth" in response.headers["location"]

@pytest.mark.asyncio
async def test_google_callback_success(unauth_client):
    with patch(
        "app.api.auth.authenticate_google_user_logic",
        return_value={"access_token": "google_access", "refresh_token": "google_refresh", "token_type": "bearer"}
    ):
        response = await unauth_client.get(
            "/api/auth/google/callback?code=mock_code",
            follow_redirects=False
        )

    assert response.status_code == 302
    assert "http://localhost/?auth=success" in response.headers["location"]
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

@pytest.mark.asyncio
async def test_login_no_password_google_user(unauth_client):
    fake_user = SimpleNamespace(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=None,
        is_active=True,
    )

    with patch("app.services.auth.get_user_by_email", return_value=fake_user):
        response = await unauth_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

    assert response.status_code == 400
    assert "linked to Google" in response.json()["detail"]
