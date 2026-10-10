from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.me import router as me_router
from app.api.customers import router as customers_router
from app.api.accounts import router as accounts_router
from app.api.transactions import router as transactions_router
from app.api.payees import router as payees_router
from app.api.transfers import router as transfers_router
from app.api.bills import router as bills_router
from app.api.loans import router as loans_router
from app.api.investments import router as investments_router
from app.api.insurance import router as insurance_router
from app.api.recommendations import router as recommendations_router
from app.api.analytics import router as analytics_router
from app.api.fraud import router as fraud_router
from app.api.compliance import router as compliance_router
from app.api.ai import router as ai_router
from app.intelligence.analytics.router import router as intelligence_analytics_router


api_router = APIRouter()

api_router.include_router(health_router)

api_router.include_router(auth_router)
api_router.include_router(me_router)

api_router.include_router(customers_router)
api_router.include_router(accounts_router)
api_router.include_router(transactions_router)
api_router.include_router(payees_router)
api_router.include_router(transfers_router)
api_router.include_router(bills_router)
api_router.include_router(loans_router)
api_router.include_router(investments_router)
api_router.include_router(insurance_router)
api_router.include_router(recommendations_router)

api_router.include_router(analytics_router)
api_router.include_router(intelligence_analytics_router)
api_router.include_router(fraud_router)
api_router.include_router(compliance_router)

api_router.include_router(ai_router)