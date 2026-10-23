import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from decimal import Decimal

from app.models.identity import User
from app.models.banking import Transaction
from app.models.intelligence import BehaviourEvent
from app.main import app
from app.core.database import get_db
from app.intelligence.analytics.constants import get_risk_label
from tests.conftest import GENERATED_PASSWORD

@pytest.fixture
async def admin_client(session_factory, seed):
    async def _get_test_db():
        async with session_factory() as session:
            yield session
    
    app.dependency_overrides[get_db] = _get_test_db
    
    # upgrade user to admin
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        user.role = "ADMIN"
        await db.commit()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": seed.user.email, "password": GENERATED_PASSWORD},
        )
        assert response.status_code == 200, response.text
        ac.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rbac_customer_forbidden(client: AsyncClient):
    # client is a CUSTOMER
    response = await client.get("/api/v1/analytics/behaviour")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_default_date_range(admin_client: AsyncClient):
    response = await admin_client.get("/api/v1/analytics/behaviour")
    assert response.status_code == 200
    data = response.json()
    assert "date_from" in data
    assert "date_to" in data
    assert "kpis" in data


@pytest.mark.asyncio
async def test_filters_narrow_results(admin_client: AsyncClient):
    # Check default active customers
    res1 = await admin_client.get("/api/v1/analytics/behaviour")
    data1 = res1.json()
    count1 = data1["kpis"]["active_customers"]

    # Filter by unlikely segment to narrow results
    res2 = await admin_client.get("/api/v1/analytics/behaviour?segment=NonExistent")
    data2 = res2.json()
    count2 = data2["kpis"]["active_customers"]

    assert count2 == 0 or count2 <= count1


@pytest.mark.asyncio
async def test_engagement_calculation(admin_client: AsyncClient):
    response = await admin_client.get("/api/v1/analytics/behaviour")
    data = response.json()
    assert "avg_engagement_pct" in data["kpis"]
    assert type(data["kpis"]["avg_engagement_pct"]) in (int, float)


@pytest.mark.asyncio
async def test_customer_top_spending_category_uses_display_label(
    admin_client: AsyncClient, seed, session_factory
):
    timestamp = datetime.now(timezone.utc)
    async with session_factory() as db:
        db.add(
            BehaviourEvent(
                customer_id=seed.customer.id,
                event_type="PAGE_VIEW",
                page="/portal/dashboard",
                action="VIEW",
                session_duration=30,
                event_metadata={},
                timestamp=timestamp,
            )
        )
        db.add(
            Transaction(
                account_id=seed.funded_account.id,
                transaction_reference="REF-ANALYTICS-TOP-CATEGORY",
                transaction_type="DEBIT",
                amount=Decimal("125.00"),
                currency="INR",
                category="GROCERIES",
                transaction_status="COMPLETED",
                transaction_date=timestamp,
            )
        )
        await db.commit()

    day = timestamp.date().isoformat()
    response = await admin_client.get(
        f"/api/v1/analytics/behaviour?date_from={day}&date_to={day}&page_size=100"
    )

    assert response.status_code == 200
    item = next(
        item
        for item in response.json()["customer_behaviour"]["items"]
        if item["customer_id"] == str(seed.customer.id)
    )
    assert item["top_spending_category"] == "Food"


@pytest.mark.asyncio
async def test_empty_data_case(admin_client: AsyncClient):
    # very future date
    response = await admin_client.get("/api/v1/analytics/behaviour?date_from=2050-01-01&date_to=2050-01-31")
    assert response.status_code == 200
    data = response.json()
    assert data["kpis"]["active_customers"] == 0
    assert data["session_analytics"]["total_sessions"] == 0
    assert len(data["page_visits"]) == 0
    assert data["customer_behaviour"]["total"] == 0


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (29, "Low"),
        (30, "Medium"),
        (59, "Medium"),
        (60, "High"),
        (79, "High"),
        (80, "Critical"),
    ],
)
def test_risk_level_boundaries(score, expected):
    assert get_risk_label(score) == expected
