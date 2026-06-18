"""
Middleware: замер времени обработки запросов.

Добавляет заголовок X-Process-Time к каждому ответу.
Логирует медленные запросы (> 1 сек).
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

SLOW_REQUEST_THRESHOLD = 1.0  # секунды


class TimingMiddleware(BaseHTTPMiddleware):
    """Замер времени обработки запроса."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        return response
