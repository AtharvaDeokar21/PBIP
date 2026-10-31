import logging
from collections.abc import Iterable
from time import perf_counter
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CollectorRegistry, Gauge, GCCollector, PlatformCollector, ProcessCollector
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from starlette.routing import Match

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, request_id_ctx

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

# Requests logged at DEBUG so health checks and scrapes don't flood the logs.
QUIET_PATHS = {"/metrics", f"{settings.api_v1_prefix}/health"}

LATENCY_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)

access_logger = logging.getLogger("credora.access")


def _route_template(app: FastAPI, request: Request) -> str | None:
    for route in app.router.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return getattr(route, "path", None)
    return None


def _add_request_middleware(app: FastAPI, inprogress: Gauge) -> None:
    """Request id, in-flight gauge and one structured access record per request."""

    @app.middleware("http")
    async def observe_request(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid4().hex
        token = request_id_ctx.set(request_id)
        route = _route_template(app, request)
        in_flight = inprogress.labels(method=request.method, handler=route or "none")
        in_flight.inc()
        start = perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            access_logger.exception("unhandled exception", extra={"method": request.method, "path": request.url.path})
            raise
        finally:
            in_flight.dec()
            path = request.url.path
            if status >= 500:
                level = logging.ERROR
            elif path in QUIET_PATHS:
                level = logging.DEBUG
            else:
                level = logging.INFO
            access_logger.log(
                level,
                "request completed",
                extra={
                    "method": request.method,
                    "path": path,
                    "route": route,
                    "status": status,
                    "duration_ms": round((perf_counter() - start) * 1000, 1),
                    "client_ip": request.client.host if request.client else None,
                },
            )
            request_id_ctx.reset(token)


def _add_metrics(app: FastAPI) -> Gauge:
    # One registry per app so several apps can live in one process (tests).
    registry = CollectorRegistry()
    ProcessCollector(registry=registry)
    PlatformCollector(registry=registry)
    GCCollector(registry=registry)

    instrumentator = Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/metrics"],
        registry=registry,
    )
    instrumentator.add(
        metrics.default(
            latency_lowr_buckets=LATENCY_BUCKETS,
            registry=registry,
        )
    )
    instrumentator.instrument(app).expose(app, include_in_schema=False)

    # The instrumentator's own in-progress gauge ignores ``registry``, so it is
    # tracked by the request middleware instead.
    return Gauge(
        "http_requests_inprogress",
        "Number of HTTP requests in progress.",
        labelnames=("method", "handler"),
        registry=registry,
    )


def create_service_app(
    *,
    service_name: str,
    service_id: str,
    description: str,
    routers: Iterable[APIRouter],
) -> FastAPI:
    """Build a FastAPI app that mounts only the given routers under /api/v1.

    Uses the same settings, exception handlers and CORS policy as the
    monolith (``app.main``), so endpoint behaviour is unchanged. Adds JSON
    request logging and a Prometheus ``/metrics`` endpoint.
    """
    configure_logging(service_id)

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

    _add_request_middleware(app, _add_metrics(app))

    return app
