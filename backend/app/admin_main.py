"""Admin service: internal analytics, fraud and compliance APIs.

Login stays on the shared ``/auth/login`` (routed to the customer service by
the gateway). The auth and /me routers are also mounted here so the service
can be used on its own, e.g. from its Swagger UI. Tokens work on both services
because they share the same JWT secret.

Run with: uvicorn app.admin_main:app
"""

from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.compliance import router as compliance_router
from app.api.fraud import router as fraud_router
from app.api.health import router as health_router
from app.api.me import router as me_router
from app.core.app_factory import create_service_app
from app.intelligence.analytics.router import (
    overview_router as intelligence_analytics_overview_router,
    router as intelligence_analytics_router,
)

ADMIN_ROUTERS = [
    health_router,
    auth_router,
    me_router,
    analytics_router,
    intelligence_analytics_router,
    intelligence_analytics_overview_router,
    fraud_router,
    compliance_router,
]

app = create_service_app(
    service_name="Admin Service",
    service_id="admin-service",
    description="Credora internal analytics, fraud and compliance APIs",
    routers=ADMIN_ROUTERS,
)
