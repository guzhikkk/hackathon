"""
  uvicorn app.main:app --reload --port 8000

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

#Мониторинг
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response

REQUESTS = Counter("http_requests_total", "Total HTTP Requests", ["method", "handler", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP Request Latency", ["method", "handler", "status"])
IN_PROGRESS = Gauge("http_requests_in_progress", "Requests in progress", ["method", "handler"])

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

    IN_PROGRESS.labels(method=method, handler=handler).inc()
    start_time = time.time()
    status_code = "500"
    try:
        response = await call_next(request)
        status_code = str(response.status_code)
        return response
    finally:
        latency = time.time() - start_time
        IN_PROGRESS.labels(method=method, handler=handler).dec()
        REQUESTS.labels(method=method, handler=handler, status=status_code).inc()
        LATENCY.labels(method=method, handler=handler, status=status_code).observe(latency)

@app.get("/metrics", include_in_schema=False)
def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

app.include_router(api_router)