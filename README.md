# 🏆 FastAPI Hackathon Boilerplate

Готовый шаблон для хакатонов на FastAPI. Разверни за 2 минуты и начни кодить фичи.

## 🔥 Что внутри

| Модуль | Описание |
|--------|----------|
| **Auth** | JWT (access + refresh), регистрация, логин |
| **Database** | PostgreSQL + async SQLAlchemy 2.0 + Alembic миграции |
| **Files** | S3/MinIO — загрузка, скачивание, presigned URLs |
| **CRUD** | Готовый User CRUD с пагинацией — копируй для новых моделей |
| **Docker** | docker-compose: app + postgres + minio за одну команду |
| **DX** | CORS, exception handlers |

## 🚀 Быстрый старт

```bash
# 1. Клонируй / скопируй шаблон
cd fastapi-hackathon-boilerplate

# 2. Скопируй конфиг
cp .env.example .env

# 3. Запусти всё через Docker
docker-compose up -d

# 4. Примени миграции
# (подожди 5 сек пока postgres стартует)
pip install -r requirements.txt
alembic revision --autogenerate -m "initial"
alembic upgrade head

# 5. Открой документацию
# Swagger UI: http://localhost:8080/docs
# MinIO UI:   http://localhost:9001 (minioadmin / minioadmin)
```

## 📁 Структура проекта

```
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Настройки из .env
│   ├── database.py          # Async SQLAlchemy
│   ├── api/                 # Роутеры
│   │   ├── router.py        # Главный роутер
│   │   ├── auth.py          # /api/auth/*
│   │   ├── users.py         # /api/users/*
│   │   └── files.py         # /api/files/*
│   ├── models/              # ORM модели
│   │   ├── base.py          # Base + миксины (ID, Timestamps)
│   │   └── user.py          # Модель User
│   ├── schemas/             # Pydantic схемы
│   │   ├── common.py        # PaginatedResponse, ErrorResponse
│   │   ├── user.py          # UserCreate, UserRead, UserUpdate
│   │   └── auth.py          # TokenPair, LoginRequest и т.д.
│   ├── services/            # Бизнес-логика
│   │   ├── auth.py          # JWT + bcrypt
│   │   ├── user.py          # CRUD пользователей
│   │   └── s3.py            # S3/MinIO клиент
│   ├── dependencies/        # FastAPI Depends
│   │   ├── auth.py          # get_current_user
│   │   └── database.py      # get_db
│   └── utils/               # Утилиты
│       └── exceptions.py    # Кастомные исключения
├── alembic/                 # Миграции БД
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
└── pyproject.toml
```

## 📖 API Эндпоинты

### Auth
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register` | Регистрация |
| POST | `/api/auth/login` | Вход (email + password) |
| POST | `/api/auth/refresh` | Обновить access токен |

### Users
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/users` | Список (пагинация) |
| GET | `/api/users/me` | Мой профиль |
| PATCH | `/api/users/me` | Обновить профиль |
| GET | `/api/users/{id}` | По ID |

### Files
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/files/upload` | Загрузить файл |
| GET | `/api/files/{key}` | Presigned URL |
| GET | `/api/files/{key}?download=true` | Скачать напрямую |
| DELETE | `/api/files/{key}` | Удалить |
| GET | `/api/files` | Список файлов |

### Health
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/` | Quick health check |
| GET | `/health` | Детальный health check |

## 🧩 Как добавить новый модуль (5 минут)

### 1. Модель (`app/models/item.py`)
```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin

class Item(IDMixin, TimestampMixin, Base):
    __tablename__ = "items"

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(2000), default="")
    # owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
```

### 2. Не забудь зарегистрировать модель (`app/models/__init__.py`)
```python
from app.models.base import Base, IDMixin, TimestampMixin
from app.models.user import User
from app.models.item import Item  # ← добавь

__all__ = ["Base", "IDMixin", "TimestampMixin", "User", "Item"]
```

### 3. Схемы (`app/schemas/item.py`)
```python
import uuid
from pydantic import BaseModel

class ItemCreate(BaseModel):
    title: str
    description: str = ""

class ItemRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    model_config = {"from_attributes": True}

class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
```

### 4. Сервис (`app/services/item.py`)
```python
# Скопируй app/services/user.py и замени User -> Item
```

### 5. Роутер (`app/api/items.py`)
```python
# Скопируй app/api/users.py и замени User -> Item
```

### 6. Подключи в роутере (`app/api/router.py`)
```python
from app.api.items import router as items_router
api_router.include_router(items_router, prefix="/items", tags=["Items"])
```

### 7. Миграция
```bash
alembic revision --autogenerate -m "add items"
alembic upgrade head
```

## 🛠 Полезные команды

```bash
# Запуск без Docker (локально)
pip install -r requirements.txt
uvicorn app.main:app --reload

# Миграции
alembic revision --autogenerate -m "описание"
alembic upgrade head
alembic downgrade -1

# Docker
docker-compose up -d          # запуск
docker-compose logs -f app    # логи
docker-compose down           # остановка
docker-compose down -v        # остановка + удаление данных

# Линтер
ruff check app/
ruff format app/
```

## 🗂 Готовые утилиты

### Кастомные исключения
```python
from app.utils.exceptions import NotFoundException, BadRequestException

raise NotFoundException("User not found")
raise BadRequestException("Invalid email format")
```

### Пагинация
```python
from app.schemas.common import PaginatedResponse

@router.get("/items", response_model=PaginatedResponse[ItemRead])
async def list_items(page: int = 1, size: int = 20):
    items, total = await get_items(db, offset=(page-1)*size, limit=size)
    return PaginatedResponse(items=items, total=total, page=page, size=size)
```

### Опциональная аутентификация
```python
from app.dependencies.auth import OptionalUser

@router.get("/feed")
async def feed(user: OptionalUser):
    if user:
        return {"feed": "personalized"}
    return {"feed": "public"}
```

## 📝 Лицензия

MIT — делай что хочешь, побеждай на хакатонах! 🏆
