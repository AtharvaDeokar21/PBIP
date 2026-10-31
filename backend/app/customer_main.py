"""Customer service: customer-facing banking APIs, shared login and the AI assistant.

Run with: uvicorn app.customer_main:app
"""

from app.api.accounts import router as accounts_router
from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.bills import router as bills_router
from app.api.customers import router as customers_router
from app.api.health import router as health_router
from app.api.insurance import router as insurance_router
from app.api.investments import router as investments_router
from app.api.loans import router as loans_router
from app.api.me import router as me_router
from app.api.payees import router as payees_router
from app.api.recommendations import router as recommendations_router
from app.api.transactions import router as transactions_router
from app.api.transfers import router as transfers_router
from app.core.app_factory import create_service_app

CUSTOMER_ROUTERS = [
    health_router,
    auth_router,
    me_router,
    customers_router,
    accounts_router,
    transactions_router,
    payees_router,
    transfers_router,
    bills_router,
    loans_router,
    investments_router,
    insurance_router,
    recommendations_router,
    ai_router,
]

app = create_service_app(
    service_name="Customer Service",
    description="Credora customer banking APIs",
    routers=CUSTOMER_ROUTERS,
)
