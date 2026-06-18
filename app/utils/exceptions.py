"""
Кастомные исключения + глобальные обработчики.

Использование:
    from app.utils.exceptions import NotFoundException, BadRequestException

    raise NotFoundException("User not found")
    raise BadRequestException("Invalid email format")

Обработчики подключаются автоматически в main.py.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


# ─── Базовые исключения ──────────────────────────────────


class AppException(Exception):
    """Базовое исключение приложения."""

    def __init__(
        self,
        message: str = "Internal server error",
        status_code: int = 500,
        detail: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(AppException):
    """404 — ресурс не найден."""

    def __init__(self, message: str = "Not found"):
        super().__init__(message=message, status_code=404)


class BadRequestException(AppException):
    """400 — некорректный запрос."""

    def __init__(self, message: str = "Bad request", detail: str | None = None):
        super().__init__(message=message, status_code=400, detail=detail)


class ForbiddenException(AppException):
    """403 — доступ запрещён."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message=message, status_code=403)


class ConflictException(AppException):
    """409 — конфликт (дубликат и т.д.)."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message=message, status_code=409)


class UnauthorizedException(AppException):
    """401 — не авторизован."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message=message, status_code=401)


# ─── Глобальные обработчики ──────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Подключить глобальные обработчики ошибок к FastAPI."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ok": False,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "ok": False,
                "message": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # В продакшене не отдаём traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "message": "Internal server error",
            },
        )
