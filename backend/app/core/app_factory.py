from collections.abc import Iterable

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # API gateway (nginx) — same-origin in normal use, listed for direct calls.
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


def create_service_app(
    *,
    service_name: str,
    description: str,
    routers: Iterable[APIRouter],
) -> FastAPI:
    """Build a FastAPI app that mounts only the given routers under /api/v1.

    Uses the same settings, exception handlers and CORS policy as the
    monolith (``app.main``), so endpoint behaviour is unchanged.
    """
    app = FastAPI(
        title=f"{settings.app_name} — {service_name}",
        version="0.4.0",
        description=description,
    )

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_router = APIRouter()
    for router in routers:
        api_router.include_router(router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/")
    async def root() -> dict:
        return {"name": settings.app_name, "service": service_name, "docs": "/docs"}

    return app
