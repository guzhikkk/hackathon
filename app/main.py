"""
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  docker-compose up
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.database import dispose_db, init_db
from app.services.s3 import s3_client

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception:
        pass

    try:
        await s3_client.ensure_bucket()
    except Exception:
        pass

    yield
    await dispose_db()


app = FastAPI(
    lifespan=lifespan,
)

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
app.include_router(api_router)