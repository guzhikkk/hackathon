"""
Главный роутер — собирает все подроутеры.

Чтобы добавить новый модуль:
  1. Создай файл app/api/my_module.py с router = APIRouter(...)
  2. Добавь сюда: from app.api.my_module import router as my_module_router
  3. Добавь: api_router.include_router(my_module_router, ...)
"""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.files import router as files_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(files_router, prefix="/files", tags=["Files"])
