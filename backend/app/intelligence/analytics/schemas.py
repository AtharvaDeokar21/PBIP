import uuid
from datetime import date
from pydantic import BaseModel
from typing import List

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
