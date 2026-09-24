from decimal import Decimal

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_customers: int
    active_customers: int
    total_accounts: int
    total_balance: Decimal
    transaction_count: int
    transaction_volume: Decimal
    fraud_alerts: int
    high_risk_customers: int


class SpendingCategory(BaseModel):
    category: str
    amount: Decimal
    transaction_count: int


class CustomerSegment(BaseModel):
    segment: str
    customer_count: int
    average_income: Decimal
    average_balance: Decimal


class TransactionTrend(BaseModel):
    period: str
    transaction_count: int
    transaction_volume: Decimal