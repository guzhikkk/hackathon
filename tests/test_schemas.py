"""Тесты Pydantic схем — валидация входных/выходных данных."""

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
from app.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
    SuccessResponse,
)
from app.schemas.user import UserCreate, UserRead, UserUpdate


# ─── Auth ────────────────────────────────────────────────


class TestAuthSchemas:

    def test_register_request_valid(self):
        data = RegisterRequest(email="user@example.com", password="pass123")
        assert data.email == "user@example.com"
        assert data.full_name == ""  # default

    def test_register_request_with_name(self):
        data = RegisterRequest(
            email="user@example.com", password="pass", full_name="John"
        )
        assert data.full_name == "John"

    def test_register_request_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="pass")

    def test_login_request_valid(self):
        data = LoginRequest(email="user@example.com", password="pass")
        assert data.email == "user@example.com"
        assert data.password == "pass"

    def test_login_request_invalid_email(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="bad", password="pass")

    def test_token_pair_defaults(self):
        data = TokenPair(access_token="abc", refresh_token="def")
        assert data.token_type == "bearer"

    def test_token_payload(self):
        data = TokenPayload(sub="user-123", exp=9999999999, type="access")
        assert data.sub == "user-123"

    def test_refresh_request(self):
        data = RefreshRequest(refresh_token="some-token")
        assert data.refresh_token == "some-token"


# ─── User ────────────────────────────────────────────────


class TestUserSchemas:

    def test_user_create_defaults(self):
        data = UserCreate(email="u@example.com", hashed_password="$2b$12$hash")
        assert data.full_name == ""
        assert data.avatar_url is None

    def test_user_read_from_orm_object(self):
        """UserRead работает с ORM-объектами (from_attributes=True)."""
        obj = SimpleNamespace(
            id=uuid.uuid4(),
            email="u@example.com",
            full_name="John",
            avatar_url=None,
            is_active=True,
            created_at=datetime(2024, 1, 1),
        )
        user = UserRead.model_validate(obj)
        assert user.email == "u@example.com"
        assert user.full_name == "John"

    def test_user_update_partial(self):
        """Обновление только переданных полей."""
        data = UserUpdate(full_name="New Name")
        dumped = data.model_dump(exclude_unset=True)
        assert "full_name" in dumped
        assert "avatar_url" not in dumped  # не передано — не включено

    def test_user_update_empty(self):
        """Пустой update — ничего не обновляется."""
        data = UserUpdate()
        assert data.model_dump(exclude_unset=True) == {}

    def test_user_update_avatar(self):
        data = UserUpdate(avatar_url="https://example.com/avatar.jpg")
        dumped = data.model_dump(exclude_unset=True)
        assert dumped["avatar_url"] == "https://example.com/avatar.jpg"


# ─── Common ─────────────────────────────────────────────


class TestCommonSchemas:

    def test_success_response_defaults(self):
        data = SuccessResponse()
        assert data.ok is True
        assert data.message == "Success"

    def test_success_response_custom_message(self):
        data = SuccessResponse(message="Done!")
        assert data.message == "Done!"

    def test_error_response(self):
        data = ErrorResponse(message="Not found")
        assert data.ok is False
        assert data.detail is None

    def test_error_response_with_detail(self):
        data = ErrorResponse(message="Bad request", detail="field 'email' required")
        assert data.detail == "field 'email' required"

    def test_paginated_response_calculates_pages(self):
        data = PaginatedResponse[str](
            items=["a", "b", "c"], total=10, page=1, size=3
        )
        assert data.pages == 4  # ceil(10/3)

    def test_paginated_response_single_page(self):
        data = PaginatedResponse[int](items=[1, 2], total=2, page=1, size=20)
        assert data.pages == 1

    def test_paginated_response_empty(self):
        data = PaginatedResponse[str](items=[], total=0, page=1, size=20)
        assert data.pages == 0

    def test_pagination_params_offset(self):
        params = PaginationParams(page=3, size=10)
        assert params.offset == 20  # (3-1) * 10
        assert params.limit == 10
