import uuid
from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    TokenPayload,
)
from app.schemas.user import UserCreate, UserRead, UserUpdate

class TestAuthSchemas:

    def test_register_request_valid(self):
        data = RegisterRequest(email="user@example.com", password="pass123")
        assert data.email == "user@example.com"
        assert data.full_name == ""  

    def test_register_request_with_name(self):
        data = RegisterRequest(
            email="user@example.com", password="pass", full_name="John"
        )
        assert data.full_name == "John"

    def test_login_request_valid(self):
        data = LoginRequest(email="user@example.com", password="pass")
        assert data.email == "user@example.com"
        assert data.password == "pass"

    def test_token_pair_defaults(self):
        data = TokenPair(access_token="abc", refresh_token="def")
        assert data.token_type == "bearer"

    def test_token_payload(self):
        data = TokenPayload(sub="user-123", exp=9999999999, type="access")
        assert data.sub == "user-123"

    def test_refresh_request(self):
        data = RefreshRequest(refresh_token="some-token")
        assert data.refresh_token == "some-token"

class TestUserSchemas:

    def test_user_create_defaults(self):
        data = UserCreate(email="u@example.com", hashed_password="$2b$12$hash")
        assert data.full_name == ""
        assert data.avatar_url is None

    def test_user_read_from_orm_object(self):
        obj = SimpleNamespace(
            id=uuid.uuid4(),
            email="u@example.com",
            user_data=SimpleNamespace(
                full_name="John",
                avatar_url=None,
            ),
            is_active=True,
            is_admin=False,
            created_at=datetime(2024, 1, 1),
        )
        user = UserRead.model_validate(obj)
        assert user.email == "u@example.com"
        assert user.user_data.full_name == "John"

    def test_user_update_partial(self):
        data = UserUpdate(full_name="New Name")
        dumped = data.model_dump(exclude_unset=True)
        assert "full_name" in dumped
        assert "avatar_url" not in dumped  

    def test_user_update_empty(self):
        data = UserUpdate()
        assert data.model_dump(exclude_unset=True) == {}

    def test_user_update_avatar(self):
        data = UserUpdate(avatar_url="https://example.com/avatar.jpg")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped["avatar_url"] == "https://example.com/avatar.jpg"
