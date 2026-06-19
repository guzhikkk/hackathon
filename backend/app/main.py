"""
  uvicorn app.main:app --reload --port 8000

  docker-compose up
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import get_settings
from app.database import dispose_db, init_db, engine
from app.services.s3 import s3_client
from sqladmin import Admin
from app.admin import AdminAuth, UserAdmin

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

# Админка
admin_auth = AdminAuth(secret_key=settings.JWT_SECRET_KEY)
admin = Admin(app, engine, authentication_backend=admin_auth)
admin.add_view(UserAdmin)

# Мониторинг
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response

REQUESTS = Counter("http_requests_total", "Total HTTP Requests", ["method", "handler", "status"])

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    method = request.method
    handler = request.url.path

    if "router" in request.scope:
        for route in request.scope["router"].routes:
            match, _ = route.matches(request.scope)
            if match.value == 2:
                if hasattr(route, "path"):
                    handler = route.path
                break

    if handler == "/metrics":
        return await call_next(request)

    status_code = "500"
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    finally:
        REQUESTS.labels(method=method, handler=handler, status=status_code).inc()

@app.get("/metrics", include_in_schema=False)
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(api_router)