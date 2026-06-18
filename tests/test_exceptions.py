"""Тесты кастомных исключений и обработчиков ошибок."""

from app.utils.exceptions import (
    AppException,
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)


class TestExceptionClasses:
    """Проверка классов исключений."""

    def test_not_found_default(self):
        exc = NotFoundException()
        assert exc.status_code == 404
        assert exc.message == "Not found"

    def test_not_found_custom_message(self):
        exc = NotFoundException("User not found")
        assert exc.message == "User not found"

    def test_bad_request_with_detail(self):
        exc = BadRequestException("Invalid data", detail="email is required")
        assert exc.status_code == 400
        assert exc.message == "Invalid data"
        assert exc.detail == "email is required"

    def test_forbidden(self):
        exc = ForbiddenException()
        assert exc.status_code == 403
        assert exc.message == "Forbidden"

    def test_conflict(self):
        exc = ConflictException("Duplicate entry")
        assert exc.status_code == 409
        assert exc.message == "Duplicate entry"

    def test_unauthorized(self):
        exc = UnauthorizedException()
        assert exc.status_code == 401
        assert exc.message == "Unauthorized"

    def test_app_exception_default(self):
        exc = AppException()
        assert exc.status_code == 500
        assert exc.message == "Internal server error"

    def test_app_exception_custom(self):
        exc = AppException(message="Custom error", status_code=418, detail="teapot")
        assert exc.status_code == 418
        assert exc.detail == "teapot"

    def test_inheritance(self):
        """Все исключения наследуют AppException и Exception."""
        exc = NotFoundException("test")
        assert isinstance(exc, AppException)
        assert isinstance(exc, Exception)

    def test_str_representation(self):
        """str(exception) возвращает сообщение."""
        exc = NotFoundException("User not found")
        assert str(exc) == "User not found"
