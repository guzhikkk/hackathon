"""
Общие схемы: пагинация, стандартные ответы, ошибки.

Используй PaginatedResponse для любых списочных эндпоинтов:

    @router.get("/items", response_model=PaginatedResponse[ItemRead])
    async def list_items(...):
        return PaginatedResponse(items=items, total=total, page=page, size=size)
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Стандартный ответ об успехе."""
    ok: bool = True
    message: str = "Success"


class ErrorResponse(BaseModel):
    """Стандартный ответ об ошибке."""
    ok: bool = False
    message: str
    detail: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Ответ с пагинацией — generic, работает с любой схемой."""
    items: list[T]
    total: int
    page: int = 1
    size: int = 20
    pages: int = 0

    def model_post_init(self, __context) -> None:
        """Автоматически считаем количество страниц."""
        if self.size > 0:
            self.pages = (self.total + self.size - 1) // self.size


class PaginationParams(BaseModel):
    """Параметры пагинации для query string."""
    page: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size
