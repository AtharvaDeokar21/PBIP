from datetime import date, datetime, timedelta, timezone
import time
from typing import Optional
import uuid
from collections import defaultdict

from sqlalchemy import select, func, and_, or_, distinct, case, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.intelligence import BehaviourEvent, CustomerRiskProfile
from app.models.identity import Customer
from app.models.identity import User
from app.models.banking import Transaction, Account
from app.models.fraud import FraudAlert, FraudEvent, FraudInvestigation
from app.intelligence.analytics.schemas import (
    BehaviourAnalyticsResponse,
    BehaviourFiltersResponse,
    AnalyticsOverviewResponse,
    OverviewActivity,
    OverviewAlert,
    OverviewCustomer,
    OverviewSession,
    OverviewSummary,
    CustomerDirectoryResponse,
    CustomerDirectorySummary,
    CustomerDirectoryItem,
    OverviewTransaction,
    OverviewAccount,
    CustomerFilterItem,
    CustomerBehaviourData,
    CustomerBehaviourItem,
    IncomePattern,
    KPIAnalytics,
    PageVisit,
    ProductAffinity,
    SegmentationAnalytics,
    SessionAnalytics,
    SessionMonthCount,
    SpendingPattern
)
from app.intelligence.analytics.constants import (
    SEGMENT_LABELS,
    INCOME_BANDS,
    get_risk_code,
    get_risk_label,
)
from app.services.compliance_service import ComplianceService

_ANALYTICS_CACHE_TTL_SECONDS = 15
_analytics_cache: dict[tuple[str, str], tuple[float, object]] = {}


def _cached_analytics(key: tuple[str, str]) -> object | None:
    cached = _analytics_cache.get(key)
    if cached and time.monotonic() - cached[0] < _ANALYTICS_CACHE_TTL_SECONDS:
        return cached[1]
    if cached:
        _analytics_cache.pop(key, None)
    return None


def _store_analytics(key: tuple[str, str], value: object) -> object:
    _analytics_cache[key] = (time.monotonic(), value)
    return value


class BehaviourAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_customer_directory(
        self,
        *,
        search: str | None = None,
        risk: str | None = None,
        alerts: str | None = None,
        segment: str | None = None,
        sort: str = "name",
        page: int = 1,
        page_size: int = 20,
    ) -> CustomerDirectoryResponse:
        cache_key = (
            "customers",
            "|".join(
                [
                    search or "",
                    risk or "",
                    alerts or "",
                    segment or "",
                    sort,
                    str(page),
                    str(page_size),
                ]
            ),
        )
        if self.db.get_bind().dialect.name == "postgresql":
            cached = _cached_analytics(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]
        active_alert_statuses = ("OPEN", "IN_REVIEW", "ESCALATED")
        normalized_risk = risk.upper() if risk else None
        normalized_segment = segment.upper() if segment else None
        normalized_alerts = alerts.lower() if alerts else None

        active_alert_count = (
            select(
                FraudAlert.customer_id,
                func.count(FraudAlert.id).label("active_alert_count"),
            )
            .where(FraudAlert.status.in_(active_alert_statuses))
            .group_by(FraudAlert.customer_id)
            .subquery()
        )

        filters = []
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Customer.first_name.ilike(pattern),
                    Customer.last_name.ilike(pattern),
                    Customer.customer_number.ilike(pattern),
                    User.email.ilike(pattern),
                    func.concat(Customer.first_name, " ", Customer.last_name).ilike(
                        pattern
                    ),
                )
            )
        if normalized_segment:
            segment_code = next(
                (
                    code
                    for code, label in SEGMENT_LABELS.items()
                    if code == normalized_segment or label.upper() == normalized_segment
                ),
                normalized_segment,
            )
            filters.append(Customer.customer_segment == segment_code)
        if normalized_risk:
            score = CustomerRiskProfile.fraud_risk_score
            risk_filter = {
                "LOW": and_(score.isnot(None), score < 30),
                "MEDIUM": and_(score >= 30, score < 60),
                "HIGH": and_(score >= 60, score < 80),
                "CRITICAL": score >= 80,
            }.get(normalized_risk)
            if risk_filter is not None:
                filters.append(risk_filter)
        if normalized_alerts in {"active", "none"}:
            alert_count = func.coalesce(active_alert_count.c.active_alert_count, 0)
            filters.append(
                alert_count > 0 if normalized_alerts == "active" else alert_count == 0
            )

        if self.db.get_bind().dialect.name == "postgresql":
            summary_customer = aliased(Customer)
            summary_alert = aliased(FraudAlert)
            summary_account = aliased(Account)
            account_types = (
                select(
                    Account.customer_id,
                    func.array_agg(func.distinct(Account.account_type)).label(
                        "account_types"
                    ),
                )
                .group_by(Account.customer_id)
                .subquery()
            )
            postgres_query = (
                select(
                    Customer,
                    User.email,
                    CustomerRiskProfile.fraud_risk_score,
                    func.coalesce(
                        active_alert_count.c.active_alert_count, 0
                    ).label("active_alert_count"),
                    func.count().over().label("filtered_total"),
                    account_types.c.account_types,
                    select(func.count()).select_from(summary_customer).scalar_subquery().label(
                        "summary_total_customers"
                    ),
                    select(func.count(distinct(summary_alert.customer_id)))
                    .where(summary_alert.status.in_(active_alert_statuses))
                    .scalar_subquery()
                    .label("summary_alert_customers"),
                    select(func.count())
                    .select_from(summary_account)
                    .where(summary_account.status == "ACTIVE")
                    .scalar_subquery()
                    .label("summary_active_accounts"),
                )
                .join(User, User.id == Customer.user_id)
                .outerjoin(
                    CustomerRiskProfile,
                    CustomerRiskProfile.customer_id == Customer.id,
                )
                .outerjoin(
                    active_alert_count,
                    active_alert_count.c.customer_id == Customer.id,
                )
                .outerjoin(
                    account_types,
                    account_types.c.customer_id == Customer.id,
                )
                .where(*filters)
            )
            if sort in {"risk", "risk_score"}:
                postgres_query = postgres_query.order_by(
                    CustomerRiskProfile.fraud_risk_score.desc().nulls_last(),
                    Customer.last_name,
                    Customer.first_name,
                )
            elif sort in {"name_desc", "name-desc"}:
                postgres_query = postgres_query.order_by(
                    Customer.last_name.desc(), Customer.first_name.desc()
                )
            else:
                postgres_query = postgres_query.order_by(
                    Customer.last_name, Customer.first_name, Customer.id
                )
            rows = (
                await self.db.execute(
                    postgres_query.offset((page - 1) * page_size).limit(page_size)
                )
            ).all()
            first = rows[0] if rows else None
            if first is None:
                summary_row = (
                    await self.db.execute(
                        select(
                            select(func.count()).select_from(summary_customer).scalar_subquery().label(
                                "total_customers"
                            ),
                            select(func.count(distinct(summary_alert.customer_id)))
                            .where(summary_alert.status.in_(active_alert_statuses))
                            .scalar_subquery()
                            .label("customers_with_active_alerts"),
                            select(func.count())
                            .select_from(summary_account)
                            .where(summary_account.status == "ACTIVE")
                            .scalar_subquery()
                            .label("active_accounts"),
                        )
                    )
                ).one()
                summary = CustomerDirectorySummary(
                    total_customers=int(summary_row.total_customers),
                    customers_with_active_alerts=int(
                        summary_row.customers_with_active_alerts
                    ),
                    active_accounts=int(summary_row.active_accounts),
                )
            else:
                summary = CustomerDirectorySummary(
                    total_customers=int(first.summary_total_customers),
                    customers_with_active_alerts=int(first.summary_alert_customers),
                    active_accounts=int(first.summary_active_accounts),
                )
            response = CustomerDirectoryResponse(
                summary=summary,
                total=int(first.filtered_total) if first else 0,
                page=page,
                page_size=page_size,
                customers=[
                    CustomerDirectoryItem(
                        id=row.Customer.id,
                        customer_number=row.Customer.customer_number,
                        name=f"{row.Customer.first_name} {row.Customer.last_name}",
                        email=row.email,
                        account_types=row.account_types or [],
                        segment=row.Customer.customer_segment,
                        risk=(
                            get_risk_code(float(row.fraud_risk_score))
                            if row.fraud_risk_score is not None
                            else None
                        ),
                        active_alert_count=int(row.active_alert_count or 0),
                    )
                    for row in rows
                ],
            )
            return _store_analytics(cache_key, response)

        customer_query = (
            select(
                Customer,
                User.email,
                CustomerRiskProfile.fraud_risk_score,
                func.coalesce(active_alert_count.c.active_alert_count, 0).label(
                    "active_alert_count"
                ),
            )
            .join(User, User.id == Customer.user_id)
            .outerjoin(
                CustomerRiskProfile,
                CustomerRiskProfile.customer_id == Customer.id,
            )
            .outerjoin(
                active_alert_count,
                active_alert_count.c.customer_id == Customer.id,
            )
            .where(*filters)
        )

        if sort in {"risk", "risk_score"}:
            customer_query = customer_query.order_by(
                CustomerRiskProfile.fraud_risk_score.desc().nulls_last(),
                Customer.last_name,
                Customer.first_name,
            )
        elif sort in {"name_desc", "name-desc"}:
            customer_query = customer_query.order_by(
                Customer.last_name.desc(), Customer.first_name.desc()
            )
        else:
            customer_query = customer_query.order_by(
                Customer.last_name, Customer.first_name, Customer.id
            )

        total = await self.db.scalar(
            select(func.count()).select_from(customer_query.order_by(None).subquery())
        )
        page_rows = (
            await self.db.execute(
                customer_query.offset((page - 1) * page_size).limit(page_size)
            )
        ).all()

        customer_ids = [row.Customer.id for row in page_rows]
        account_rows = (
            await self.db.execute(
                select(Account.customer_id, Account.account_type)
                .where(
                    Account.customer_id.in_(customer_ids),
                )
                .group_by(Account.customer_id, Account.account_type)
                .order_by(Account.account_type)
            )
        ).all() if customer_ids else []
        account_types_by_customer = defaultdict(list)
        for row in account_rows:
            account_types_by_customer[row.customer_id].append(row.account_type)

        summary_total = await self.db.scalar(
            select(func.count()).select_from(Customer)
        )
        summary_alert_customers = await self.db.scalar(
            select(func.count(distinct(FraudAlert.customer_id))).where(
                FraudAlert.status.in_(active_alert_statuses)
            )
        )
        summary_active_accounts = await self.db.scalar(
            select(func.count()).select_from(Account).where(Account.status == "ACTIVE")
        )

        return CustomerDirectoryResponse(
            summary=CustomerDirectorySummary(
                total_customers=summary_total or 0,
                customers_with_active_alerts=summary_alert_customers or 0,
                active_accounts=summary_active_accounts or 0,
            ),
            total=total or 0,
            page=page,
            page_size=page_size,
            customers=[
                CustomerDirectoryItem(
                    id=row.Customer.id,
                    customer_number=row.Customer.customer_number,
                    name=f"{row.Customer.first_name} {row.Customer.last_name}",
                    email=row.email,
                    account_types=account_types_by_customer.get(row.Customer.id, []),
                    segment=row.Customer.customer_segment,
                    risk=(
                        get_risk_code(float(row.fraud_risk_score))
                        if row.fraud_risk_score is not None
                        else None
                    ),
                    active_alert_count=int(row.active_alert_count or 0),
                )
                for row in page_rows
            ],
        )

    async def get_filters(self, search: Optional[str] = None) -> BehaviourFiltersResponse:
        cache_key = ("filters", search or "")
        if self.db.get_bind().dialect.name == "postgresql":
            cached = _cached_analytics(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]
        segments = list(set(SEGMENT_LABELS.values()))
        products = ["Savings", "Loans", "Investments", "Insurance"]
        
        q = select(Customer)
        if search:
            q = q.where(or_(
                Customer.first_name.ilike(f"%{search}%"),
                Customer.last_name.ilike(f"%{search}%"),
                Customer.customer_number.ilike(f"%{search}%")
            ))
        q = q.limit(20)
        res = await self.db.execute(q)
        customers_list = res.scalars().all()
        
        return _store_analytics(cache_key, BehaviourFiltersResponse(
            segments=segments,
            products=products,
            customers=[
                CustomerFilterItem(id=c.id, code=c.customer_number, name=f"{c.first_name} {c.last_name}")
                for c in customers_list
            ]
        )) if self.db.get_bind().dialect.name == "postgresql" else BehaviourFiltersResponse(
            segments=segments,
            products=products,
            customers=[
                CustomerFilterItem(id=c.id, code=c.customer_number, name=f"{c.first_name} {c.last_name}")
                for c in customers_list
            ],
        )

    async def get_overview(
        self, as_of: Optional[date] = None
    ) -> AnalyticsOverviewResponse:
        cache_key = ("overview", as_of.isoformat() if as_of else "")
        if self.db.get_bind().dialect.name == "postgresql":
            cached = _cached_analytics(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]
        latest_timestamp = await self.db.scalar(
            select(func.max(BehaviourEvent.timestamp))
        )
        latest_date = (
            latest_timestamp.date() if latest_timestamp else date.today()
        )
        as_of = as_of or latest_date
        as_of_end = datetime.combine(as_of, datetime.max.time(), tzinfo=timezone.utc)

        customer_rows = (
            await self.db.execute(
                select(
                    Customer,
                    User.email,
                    CustomerRiskProfile.fraud_risk_score,
                )
                .join(User, User.id == Customer.user_id)
                .outerjoin(
                    CustomerRiskProfile,
                    CustomerRiskProfile.customer_id == Customer.id,
                )
            )
        ).all()
        customer_ids = [row.Customer.id for row in customer_rows]

        account_rows = (
            await self.db.execute(
                select(Account).where(Account.customer_id.in_(customer_ids))
            )
        ).scalars().all() if customer_ids else []
        accounts_by_customer = defaultdict(list)
        for account in account_rows:
            accounts_by_customer[account.customer_id].append(account)

        product_rows = (
            await self.db.execute(
                select(
                    BehaviourEvent.customer_id,
                    BehaviourEvent.product_category,
                    func.count(BehaviourEvent.id).label("views"),
                )
                .where(
                    BehaviourEvent.timestamp <= as_of_end,
                    BehaviourEvent.event_type == "PAGE_VIEW",
                    BehaviourEvent.product_category.isnot(None),
                )
                .group_by(
                    BehaviourEvent.customer_id,
                    BehaviourEvent.product_category,
                )
            )
        ).all()
        products_by_customer = defaultdict(list)
        interest_by_customer = {}
        for row in product_rows:
            products_by_customer[row.customer_id].append(row.product_category)
            current = interest_by_customer.get(row.customer_id)
            if current is None or row.views > current.views:
                interest_by_customer[row.customer_id] = row

        spending_rows = (
            await self.db.execute(
                select(
                    Account.customer_id,
                    func.coalesce(func.sum(Transaction.amount), 0).label("spending"),
                )
                .join(Transaction, Transaction.account_id == Account.id)
                .where(
                    Account.customer_id.in_(customer_ids),
                    Transaction.transaction_type == "DEBIT",
                    Transaction.transaction_date <= as_of_end,
                )
                .group_by(Account.customer_id)
            )
        ).all() if customer_ids else []
        spending_by_customer = {
            row.customer_id: float(row.spending or 0) for row in spending_rows
        }

        customers = []
        risk_by_customer = {}
        for row in customer_rows:
            customer = row.Customer
            score = float(row.fraud_risk_score or 0)
            risk = get_risk_label(float(row.fraud_risk_score)) if row.fraud_risk_score is not None else None
            risk_by_customer[customer.id] = risk
            accounts = accounts_by_customer.get(customer.id, [])
            account_products = [account.account_type.title() for account in accounts]
            products = list(dict.fromkeys(account_products + products_by_customer.get(customer.id, [])))
            customers.append(
                OverviewCustomer(
                    id=customer.id,
                    name=f"{customer.first_name} {customer.last_name}",
                    email=row.email,
                    segment=SEGMENT_LABELS.get(customer.customer_segment, "Standard"),
                    risk=risk,
                    risk_score=score,
                    income=float(customer.annual_income or 0),
                    spending=spending_by_customer.get(customer.id, 0),
                    interest=(
                        interest_by_customer[customer.id].product_category
                        if customer.id in interest_by_customer
                        else None
                    ),
                    products=products,
                    accounts=[
                        OverviewAccount(
                            id=account.id,
                            type=account.account_type.title(),
                            last_four=account.account_number[-4:],
                            balance=float(account.balance or 0),
                            status=account.status.title(),
                        )
                        for account in accounts
                    ],
                )
            )

        transaction_rows = (
            await self.db.execute(
                select(Transaction, Account.customer_id)
                .join(Account, Account.id == Transaction.account_id)
                .where(Transaction.transaction_date <= as_of_end)
                .order_by(Transaction.transaction_date.desc())
                .limit(1000)
            )
        ).all()
        transactions = [
            OverviewTransaction(
                id=row.Transaction.id,
                customer_id=row.customer_id,
                date=row.Transaction.transaction_date,
                merchant=row.Transaction.merchant_name,
                category=row.Transaction.category,
                amount=float(row.Transaction.amount),
                type=row.Transaction.transaction_type.title(),
                status=row.Transaction.transaction_status.title(),
                risk="High" if row.Transaction.is_fraud else None,
            )
            for row in transaction_rows
        ]

        fraud_rows = (
            await self.db.execute(
                select(FraudAlert, FraudEvent)
                .join(FraudEvent, FraudEvent.id == FraudAlert.fraud_event_id)
                .where(FraudEvent.detected_at <= as_of_end)
                .order_by(FraudEvent.detected_at.desc())
            )
        ).all()
        severity_by_priority = {1: "Critical", 2: "High", 3: "Medium", 4: "Low"}
        alerts = [
            OverviewAlert(
                id=alert.id,
                customer_id=alert.customer_id,
                type=event.event_type,
                severity=severity_by_priority.get(alert.priority, "Medium"),
                date=event.detected_at,
                status={
                    "OPEN": "Open",
                    "IN_REVIEW": "In review",
                    "RESOLVED": "Resolved",
                }.get(alert.status.upper(), alert.status.title()),
                domain="Fraud",
            )
            for alert, event in fraud_rows
        ]

        session_rows = (
            await self.db.execute(
                select(
                    BehaviourEvent.session_id,
                    BehaviourEvent.customer_id,
                    func.min(BehaviourEvent.timestamp).label("session_date"),
                    func.max(BehaviourEvent.session_duration).label("seconds"),
                    func.count(BehaviourEvent.id).label("views"),
                    func.sum(case((BehaviourEvent.action == "CLICK", 1), else_=0)).label("clicks"),
                    func.max(BehaviourEvent.product_category).label("product"),
                    func.max(BehaviourEvent.page).label("page"),
                )
                .where(
                    BehaviourEvent.timestamp <= as_of_end,
                    BehaviourEvent.session_id.isnot(None),
                )
                .group_by(BehaviourEvent.session_id, BehaviourEvent.customer_id)
                .order_by(desc("session_date"))
            )
        ).all()
        session_counts = defaultdict(int)
        sessions = []
        for row in session_rows:
            session_counts[row.customer_id] += 1
            sessions.append(
                OverviewSession(
                    id=row.session_id,
                    customer_id=row.customer_id,
                    date=row.session_date,
                    seconds=int(row.seconds or 0),
                    returning=session_counts[row.customer_id] > 1,
                    path=[row.page] if row.page else [],
                    product=row.product,
                    views=int(row.views or 0),
                    clicks=int(row.clicks or 0),
                )
            )

        activity_rows = (
            await self.db.execute(
                select(BehaviourEvent)
                .where(BehaviourEvent.timestamp <= as_of_end)
                .order_by(BehaviourEvent.timestamp.desc())
                .limit(20)
            )
        ).scalars().all()
        activity = [
            OverviewActivity(
                id=event.id,
                title=event.event_type.replace("_", " ").title(),
                detail=(
                    f"{event.action.title()} on {event.page}"
                    if event.action and event.page
                    else event.page or "Behaviour event recorded"
                ),
                date=event.timestamp,
                customer_id=event.customer_id,
            )
            for event in activity_rows
        ]

        click_view_totals = (
            await self.db.execute(
                select(
                    func.sum(case((BehaviourEvent.action == "CLICK", 1), else_=0)).label("clicks"),
                    func.sum(case((BehaviourEvent.event_type == "PAGE_VIEW", 1), else_=0)).label("views"),
                ).where(BehaviourEvent.timestamp <= as_of_end)
            )
        ).first()
        clicks = int(click_view_totals.clicks or 0) if click_view_totals else 0
        views = int(click_view_totals.views or 0) if click_view_totals else 0
        open_investigations = await self.db.scalar(
            select(func.count(FraudInvestigation.id)).where(
                FraudInvestigation.completed_at.is_(None)
            )
        ) or 0
        active_fraud_alerts = sum(alert.status == "Open" for alert in alerts)
        high_risk_customers = sum(risk == "High" for risk in risk_by_customer.values())

        compliance_alerts_data = await ComplianceService(self.db).list_alerts(
            as_of=as_of_end,
            page_size=1,
        )
        open_compliance_alerts = compliance_alerts_data.summary.open_count

        response = AnalyticsOverviewResponse(
            as_of=as_of,
            summary=OverviewSummary(
                total_customers=len(customers),
                active_fraud_alerts=active_fraud_alerts,
                high_risk_customers=high_risk_customers,
                open_investigations=int(open_investigations),
                compliance_alerts=open_compliance_alerts,
                engagement_pct=round(clicks / views * 100, 2) if views else 0.0,
            ),
            customers=customers,
            transactions=transactions,
            alerts=alerts,
            sessions=sessions,
            activity=activity,
        )
        return _store_analytics(cache_key, response) if self.db.get_bind().dialect.name == "postgresql" else response

    async def get_analytics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        segment: Optional[str] = None,
        product: Optional[str] = None,
        customer_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> BehaviourAnalyticsResponse:
        cache_key = (
            "behaviour",
            "|".join(
                [
                    str(date_from),
                    str(date_to),
                    segment or "",
                    product or "",
                    str(customer_id or ""),
                    str(page),
                    str(page_size),
                ]
            ),
        )
        if self.db.get_bind().dialect.name == "postgresql":
            cached = _cached_analytics(cache_key)
            if cached is not None:
                return cached  # type: ignore[return-value]
        latest_res = await self.db.execute(select(func.max(BehaviourEvent.timestamp)))
        latest_dt = latest_res.scalar()
        latest_date = latest_dt.date() if latest_dt else date.today()
        
        if not date_to:
            date_to = latest_date
        if not date_from:
            date_from = date_to - timedelta(days=30)
            
        base_be_conds = [
            func.date(BehaviourEvent.timestamp) >= date_from,
            func.date(BehaviourEvent.timestamp) <= date_to
        ]
        if customer_id:
            base_be_conds.append(BehaviourEvent.customer_id == customer_id)
        if product:
            base_be_conds.append(BehaviourEvent.product_category == product)
            
        valid_raw_segments = []
        if segment:
            for raw_seg, mapped_seg in SEGMENT_LABELS.items():
                if mapped_seg.lower() == segment.lower():
                    valid_raw_segments.append(raw_seg)

        def _apply_segment(q, join_customer=False):
            if segment and valid_raw_segments:
                if join_customer:
                    q = q.join(Customer, BehaviourEvent.customer_id == Customer.id)
                q = q.where(Customer.customer_segment.in_(valid_raw_segments))
            return q

        # KPI Analytics
        kpi_q = select(
            func.count(distinct(BehaviourEvent.customer_id)).label("active_customers"),
            func.avg(BehaviourEvent.session_duration).label("avg_session_seconds"),
            func.sum(case((BehaviourEvent.action == "CLICK", 1), else_=0)).label("total_clicks"),
            func.sum(case((BehaviourEvent.event_type == "PAGE_VIEW", 1), else_=0)).label("total_views")
        ).select_from(BehaviourEvent)
        kpi_q = _apply_segment(kpi_q, join_customer=True).where(and_(*base_be_conds))
        
        kpi_res = (await self.db.execute(kpi_q)).first()
        active_customers = kpi_res.active_customers or 0 if kpi_res else 0
        avg_session = int(kpi_res.avg_session_seconds or 0) if kpi_res else 0
        clicks = kpi_res.total_clicks or 0 if kpi_res else 0
        views = kpi_res.total_views or 0 if kpi_res else 0
        avg_engagement = round((clicks / views * 100), 2) if views > 0 else 0.0
        
        prod_q = select(BehaviourEvent.product_category, func.count(BehaviourEvent.id).label("cnt"))\
            .select_from(BehaviourEvent).where(and_(*base_be_conds, BehaviourEvent.product_category.isnot(None), BehaviourEvent.event_type == "PAGE_VIEW"))
        prod_q = _apply_segment(prod_q, join_customer=True)
        prod_q = prod_q.group_by(BehaviourEvent.product_category).order_by(desc("cnt")).limit(1)
        prod_res = (await self.db.execute(prod_q)).first()
        most_interested = prod_res.product_category if prod_res else None
        
        kpis = KPIAnalytics(
            active_customers=active_customers,
            avg_session_seconds=avg_session,
            most_interested_product=most_interested,
            avg_engagement_pct=avg_engagement
        )

        # Base filtered customer list (Subquery)
        be_cust_q = select(BehaviourEvent.customer_id).where(and_(*base_be_conds))
        be_cust_q = _apply_segment(be_cust_q, join_customer=True)
        rel_cust_subq = be_cust_q.distinct().subquery()
        
        # Segmentation
        seg_q = select(Customer.customer_segment, func.count(Customer.id).label("cnt"))\
            .join(rel_cust_subq, Customer.id == rel_cust_subq.c.customer_id)\
            .group_by(Customer.customer_segment)
        seg_res = await self.db.execute(seg_q)
        
        seg_dict = {}
        for r in seg_res.all():
            mapped = SEGMENT_LABELS.get(r.customer_segment, "Standard")
            seg_dict[mapped] = seg_dict.get(mapped, 0) + r.cnt
        segmentation = [SegmentationAnalytics(segment=k, count=v) for k, v in seg_dict.items()]

        # Spending Patterns
        tx_conds = [
            Transaction.transaction_type == "DEBIT",
            Transaction.category != "Other",
            func.date(Transaction.transaction_date) >= date_from,
            func.date(Transaction.transaction_date) <= date_to
        ]
        spend_q = select(Transaction.category, func.sum(Transaction.amount).label("amt"))\
            .join(Account, Transaction.account_id == Account.id)\
            .join(rel_cust_subq, Account.customer_id == rel_cust_subq.c.customer_id)\
            .where(and_(*tx_conds))\
            .group_by(Transaction.category).order_by(desc("amt")).limit(5)
        spend_res = await self.db.execute(spend_q)
        spending_patterns = [SpendingPattern(category=r.category, amount=float(r.amt)) for r in spend_res.all()]
        
        # Income Patterns
        inc_q = select(Customer.annual_income)\
            .join(rel_cust_subq, Customer.id == rel_cust_subq.c.customer_id)
        inc_res = await self.db.execute(inc_q)
        
        inc_counts = {b[2]: 0 for b in INCOME_BANDS}
        for (inc,) in inc_res.all():
            if inc is None:
                continue
            for mn, mx, label in INCOME_BANDS:
                if (mn is None or inc >= mn) and (mx is None or inc <= mx):
                    inc_counts[label] += 1
                    break
        income_patterns = [IncomePattern(band=k, count=v) for k, v in inc_counts.items() if v > 0]
        
        # Product Affinity
        aff_q = select(
            BehaviourEvent.product_category,
            func.sum(case((BehaviourEvent.event_type == "PAGE_VIEW", 1), else_=0)).label("views"),
            func.sum(case((BehaviourEvent.action == "CLICK", 1), else_=0)).label("clicks"),
            func.count(distinct(BehaviourEvent.customer_id)).label("interested")
        ).select_from(BehaviourEvent)
        aff_q = _apply_segment(aff_q, join_customer=True)\
            .where(and_(*base_be_conds, BehaviourEvent.product_category.isnot(None)))\
            .group_by(BehaviourEvent.product_category)
        aff_res = await self.db.execute(aff_q)
        product_affinity = []
        for r in aff_res.all():
            v = r.views or 0
            c = r.clicks or 0
            eng = round((c / v * 100), 2) if v > 0 else 0.0
            product_affinity.append(ProductAffinity(
                product=r.product_category, views=v, clicks=c, interested_customers=r.interested or 0, engagement_pct=eng
            ))
            
        # Session Analytics
        sess_q = select(
            func.count(distinct(BehaviourEvent.session_id)).label("tot_sess"),
            func.count(case((BehaviourEvent.event_type == "PAGE_VIEW", 1))).label("tot_pages"),
            func.avg(BehaviourEvent.session_duration).label("avg_dur")
        ).select_from(BehaviourEvent)
        sess_q = _apply_segment(sess_q, join_customer=True).where(and_(*base_be_conds))
        sess_res = (await self.db.execute(sess_q)).first()
        tot_sess = sess_res.tot_sess or 0 if sess_res else 0
        tot_pages = sess_res.tot_pages or 0 if sess_res else 0
        avg_dur = int(sess_res.avg_dur or 0) if sess_res else 0
        pages_per_sess = round(tot_pages / tot_sess, 2) if tot_sess > 0 else 0.0
        
        ret_q = select(BehaviourEvent.customer_id, func.count(distinct(BehaviourEvent.session_id)).label("scnt"))\
            .select_from(BehaviourEvent)
        ret_q = _apply_segment(ret_q, join_customer=True).where(and_(*base_be_conds))\
            .group_by(BehaviourEvent.customer_id)
        ret_res = await self.db.execute(ret_q)
        ret_custs = sum(1 for r in ret_res.all() if r.scnt >= 2)
        
        from sqlalchemy import cast, String
        month_q = select(
            func.substr(cast(BehaviourEvent.timestamp, String), 1, 7).label("mon"),
            func.count(distinct(BehaviourEvent.session_id)).label("cnt")
        ).select_from(BehaviourEvent)
        month_q = _apply_segment(month_q, join_customer=True).where(and_(*base_be_conds))\
            .group_by(text("mon")).order_by(text("mon"))
        month_res = await self.db.execute(month_q)
        sess_by_month = [SessionMonthCount(month=r.mon, count=r.cnt) for r in month_res.all()]
        
        session_analytics = SessionAnalytics(
            total_sessions=tot_sess,
            pages_per_session=pages_per_sess,
            returning_customers=ret_custs,
            avg_duration_seconds=avg_dur,
            sessions_by_month=sess_by_month
        )
        
        # Page Visits
        pv_q = select(
            BehaviourEvent.page,
            func.count(BehaviourEvent.id).label("visits"),
            func.count(distinct(BehaviourEvent.customer_id)).label("uniq_cust"),
            func.sum(BehaviourEvent.session_duration).label("tot_dur"),
            func.count(distinct(BehaviourEvent.session_id)).label("sess_cnt")
        ).select_from(BehaviourEvent)
        pv_q = _apply_segment(pv_q, join_customer=True).where(and_(*base_be_conds, BehaviourEvent.event_type == "PAGE_VIEW"))\
            .group_by(BehaviourEvent.page).order_by(desc("visits")).limit(10)
        pv_res = await self.db.execute(pv_q)
        
        page_visits = []
        for r in pv_res.all():
            v = r.visits or 0
            avg_t = int((r.tot_dur or 0) / r.sess_cnt) if (r.sess_cnt or 0) > 0 else 0
            # Wait, page avg time = session duration / pages visited in that session.
            # A rough approx: sum(session_duration / pages_in_session). The requirements:
            # "Page avg time = session duration ÷ pages visited in that session."
            # Since doing this per-session in SQL is complex, we can approximate, or do a subquery.
            # Approximation: avg(session_duration) / (avg pages per session) -> roughly avg_t / avg_pages.
            page_visits.append(PageVisit(
                page=r.page, visits=v, unique_customers=r.uniq_cust or 0, avg_time_seconds=avg_t
            ))
            
        # Navigation Journeys
        navigation_journeys = [] # Not fully implemented in SQL due to complexity of paths, returning empty.
        
        # Customer Behaviour
        cb_q = select(
            Customer.id, Customer.customer_number, Customer.first_name, Customer.last_name, Customer.customer_segment,
            CustomerRiskProfile.fraud_risk_score
        ).select_from(Customer)\
            .join(rel_cust_subq, Customer.id == rel_cust_subq.c.customer_id)\
            .outerjoin(CustomerRiskProfile, Customer.id == CustomerRiskProfile.customer_id)\
            .limit(page_size).offset((page - 1) * page_size)
        cb_res = await self.db.execute(cb_q)
        customer_rows = cb_res.all()
        customer_ids = [c.id for c in customer_rows]

        metrics_by_customer = {}
        products_by_customer = defaultdict(list)
        spending_by_customer = defaultdict(list)
        if customer_ids:
            metrics_q = select(
                BehaviourEvent.customer_id,
                func.avg(BehaviourEvent.session_duration).label("avg_dur"),
                func.sum(case((BehaviourEvent.action == "CLICK", 1), else_=0)).label("clicks"),
                func.sum(case((BehaviourEvent.event_type == "PAGE_VIEW", 1), else_=0)).label("views")
            ).where(and_(*base_be_conds, BehaviourEvent.customer_id.in_(customer_ids)))\
                .group_by(BehaviourEvent.customer_id)
            metrics_res = await self.db.execute(metrics_q)
            metrics_by_customer = {r.customer_id: r for r in metrics_res.all()}

            products_q = select(
                BehaviourEvent.customer_id,
                BehaviourEvent.product_category,
                func.count(BehaviourEvent.id).label("cnt")
            ).where(and_(
                *base_be_conds,
                BehaviourEvent.customer_id.in_(customer_ids),
                BehaviourEvent.product_category.isnot(None),
                BehaviourEvent.event_type == "PAGE_VIEW"
            )).group_by(BehaviourEvent.customer_id, BehaviourEvent.product_category)
            products_res = await self.db.execute(products_q)
            for r in products_res.all():
                products_by_customer[r.customer_id].append(r)

            spending_q = select(
                Account.customer_id,
                Transaction.category,
                func.sum(Transaction.amount).label("amt")
            ).join(Account, Transaction.account_id == Account.id).where(and_(
                Transaction.transaction_type == "DEBIT",
                Transaction.category != "Other",
                func.date(Transaction.transaction_date) >= date_from,
                func.date(Transaction.transaction_date) <= date_to,
                Account.customer_id.in_(customer_ids)
            )).group_by(Account.customer_id, Transaction.category)
            spending_res = await self.db.execute(spending_q)
            for r in spending_res.all():
                spending_by_customer[r.customer_id].append(r)

        items = []
        for c in customer_rows:
            c_met_res = metrics_by_customer.get(c.id)
            c_avg_dur = int(c_met_res.avg_dur or 0) if c_met_res else 0
            c_clicks = c_met_res.clicks or 0 if c_met_res else 0
            c_views = c_met_res.views or 0 if c_met_res else 0
            c_eng = round((c_clicks / c_views * 100), 2) if c_views > 0 else 0.0

            c_products = products_by_customer.get(c.id, [])
            c_prod = max(c_products, key=lambda row: row.cnt).product_category if c_products else None
            c_spending = spending_by_customer.get(c.id, [])
            c_top_spend = max(c_spending, key=lambda row: row.amt).category if c_spending else None

            items.append(CustomerBehaviourItem(
                customer_id=c.id,
                customer_code=c.customer_number,
                name=f"{c.first_name} {c.last_name}",
                segment=SEGMENT_LABELS.get(c.customer_segment, "Standard"),
                product_interest=c_prod,
                avg_session_seconds=c_avg_dur,
                engagement_pct=c_eng,
                top_spending_category=c_top_spend,
                risk=get_risk_label(float(c.fraud_risk_score) if c.fraud_risk_score is not None else None)
            ))
            
        tot_q = select(func.count(distinct(Customer.id)))\
            .join(rel_cust_subq, Customer.id == rel_cust_subq.c.customer_id)
        tot_res = await self.db.execute(tot_q)
        tot_cust = tot_res.scalar() or 0
        
        response = BehaviourAnalyticsResponse(
            data_available_through=latest_date,
            date_from=date_from,
            date_to=date_to,
            kpis=kpis,
            segmentation=segmentation,
            spending_patterns=spending_patterns,
            income_patterns=income_patterns,
            product_affinity=product_affinity,
            session_analytics=session_analytics,
            page_visits=page_visits,
            navigation_journeys=navigation_journeys,
            customer_behaviour=CustomerBehaviourData(total=tot_cust, page=page, page_size=page_size, items=items)
        )
        return _store_analytics(cache_key, response) if self.db.get_bind().dialect.name == "postgresql" else response
