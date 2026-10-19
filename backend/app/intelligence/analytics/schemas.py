import uuid
from datetime import date, datetime
from pydantic import BaseModel
from typing import List


def _to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.title() for part in tail)


class _OverviewModel(BaseModel):
    model_config = {
        "alias_generator": _to_camel,
        "populate_by_name": True,
    }

class KPIAnalytics(BaseModel):
    active_customers: int
    avg_session_seconds: int
    most_interested_product: str | None
    avg_engagement_pct: float

class SegmentationAnalytics(BaseModel):
    segment: str
    count: int

class SpendingPattern(BaseModel):
    category: str
    amount: float

class IncomePattern(BaseModel):
    band: str
    count: int

class ProductAffinity(BaseModel):
    product: str
    views: int
    clicks: int
    interested_customers: int
    engagement_pct: float

class SessionMonthCount(BaseModel):
    month: str
    count: int

class SessionAnalytics(BaseModel):
    total_sessions: int
    pages_per_session: float
    returning_customers: int
    avg_duration_seconds: int
    sessions_by_month: List[SessionMonthCount]

class PageVisit(BaseModel):
    page: str
    visits: int
    unique_customers: int
    avg_time_seconds: int

class NavigationJourney(BaseModel):
    path: List[str]
    sessions: int

class CustomerBehaviourItem(BaseModel):
    customer_id: uuid.UUID
    customer_code: str
    name: str
    segment: str
    product_interest: str | None
    avg_session_seconds: int
    engagement_pct: float
    top_spending_category: str | None
    risk: str | None

class CustomerBehaviourData(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CustomerBehaviourItem]

class BehaviourAnalyticsResponse(BaseModel):
    data_available_through: date
    date_from: date
    date_to: date
    kpis: KPIAnalytics
    segmentation: List[SegmentationAnalytics]
    spending_patterns: List[SpendingPattern]
    income_patterns: List[IncomePattern]
    product_affinity: List[ProductAffinity]
    session_analytics: SessionAnalytics
    page_visits: List[PageVisit]
    navigation_journeys: List[NavigationJourney]
    customer_behaviour: CustomerBehaviourData

class CustomerFilterItem(BaseModel):
    id: uuid.UUID
    code: str
    name: str

class BehaviourFiltersResponse(BaseModel):
    segments: List[str]
    products: List[str]
    customers: List[CustomerFilterItem]


class CustomerDirectorySummary(_OverviewModel):
    total_customers: int
    customers_with_active_alerts: int
    active_accounts: int


class CustomerDirectoryItem(_OverviewModel):
    id: uuid.UUID
    customer_number: str
    name: str
    email: str
    account_types: List[str]
    segment: str | None
    risk: str | None
    active_alert_count: int


class CustomerDirectoryResponse(_OverviewModel):
    summary: CustomerDirectorySummary
    total: int
    page: int
    page_size: int
    customers: List[CustomerDirectoryItem]


class OverviewAccount(_OverviewModel):
    id: uuid.UUID
    type: str
    last_four: str
    balance: float
    status: str


class MonthlyFinancialTrend(_OverviewModel):
    month: str
    amount: float


class OverviewCustomer(_OverviewModel):
    id: uuid.UUID
    name: str
    email: str
    segment: str
    risk: str | None
    risk_score: float
    income: float
    spending: float
    spending_insights: List[SpendingPattern]
    monthly_income_trend: List["MonthlyFinancialTrend"]
    monthly_spending_trend: List["MonthlyFinancialTrend"]
    interest: str | None
    products: List[str]
    accounts: List[OverviewAccount]


class OverviewTransaction(_OverviewModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    date: datetime
    merchant: str | None
    category: str | None
    amount: float
    type: str
    status: str
    risk: str | None


class OverviewAlert(_OverviewModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    type: str
    severity: str
    date: datetime
    status: str
    domain: str


class OverviewSession(_OverviewModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    date: datetime
    seconds: int
    returning: bool
    path: List[str]
    product: str | None
    views: int
    clicks: int


class OverviewActivity(_OverviewModel):
    id: uuid.UUID
    title: str
    detail: str
    date: datetime
    customer_id: uuid.UUID


class OverviewSummary(_OverviewModel):
    total_customers: int
    active_fraud_alerts: int
    high_risk_customers: int
    open_investigations: int
    compliance_alerts: int
    engagement_pct: float


class AnalyticsOverviewResponse(_OverviewModel):
    as_of: date
    summary: OverviewSummary
    customers: List[OverviewCustomer]
    transactions: List[OverviewTransaction]
    alerts: List[OverviewAlert]
    sessions: List[OverviewSession]
    activity: List[OverviewActivity]
