from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.error_handlers import register_exception_handlers
from app.middleware.request_context import RequestContextMiddleware
from app.workers.runtime import outbox_worker

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.monitoring_outbox_worker_enabled:
        outbox_worker.start()
    yield
    if settings.monitoring_outbox_worker_enabled:
        await outbox_worker.stop()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug or settings.is_development else None,
    redoc_url="/redoc" if settings.debug or settings.is_development else None,
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
