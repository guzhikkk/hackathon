"""
FastAPI Hackathon Boilerplate — точка входа.

Запуск:
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Или через Docker:
  docker-compose up
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.database import dispose_db, init_db
from app.services.s3 import s3_client
from app.utils.exceptions import register_exception_handlers

settings = get_settings()


# ─── Lifespan (startup / shutdown) ───────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle: инициализация при старте, очистка при остановке."""
    # Startup
    try:
        await init_db()
    except Exception:
        pass

    try:
        await s3_client.ensure_bucket()
    except Exception:
        pass

    yield

    # Shutdown
    await dispose_db()


# ─── App ─────────────────────────────────────────────────


app = FastAPI(
    lifespan=lifespan,
)

# ─── Middleware ──────────────────────────────────────────

# CORS — разрешаем всё (для хакатона это ок)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Exception Handlers ─────────────────────────────────

register_exception_handlers(app)

# ─── Routes ──────────────────────────────────────────────

app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Health check."""
    return {
        "status": "ok",
    }

