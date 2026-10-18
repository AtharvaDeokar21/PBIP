from decimal import Decimal
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_db
from app.main import app
from app.models.fraud import FraudAlert, FraudEvent
from app.models.identity import Customer, User
from app.models.intelligence import BehaviourEvent, CustomerRiskProfile
from tests.conftest import GENERATED_PASSWORD


@pytest.fixture
async def admin_client(session_factory, seed):
    async def _get_test_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        user.role = "ADMIN"
        customers = list(await db.scalars(select(Customer).order_by(Customer.created_at)))
        customers[0].customer_segment = "MASS_MARKET"
        customers[1].customer_segment = "HIGH_NET_WORTH"
        db.add(
            CustomerRiskProfile(
                customer_id=customers[0].id,
                fraud_risk_score=Decimal("85"),
            )
        )
        db.add(
            CustomerRiskProfile(
                customer_id=customers[1].id,
                fraud_risk_score=Decimal("45"),
            )
        )
        event = FraudEvent(
            customer_id=customers[0].id,
            event_type="SUSPICIOUS_LOGIN",
            risk_score=Decimal("85"),
            severity="HIGH",
            detected_at=seed.user.created_at,
        )
        db.add(event)
        await db.flush()
        db.add(
            FraudAlert(
                fraud_event_id=event.id,
                customer_id=customers[0].id,
                status="OPEN",
            )
        )
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": seed.user.email, "password": GENERATED_PASSWORD},
        )
        assert response.status_code == 200
        client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_customer_directory_counts_search_filters_and_pagination(
    admin_client, session_factory
):
    response = await admin_client.get(
        "/api/v1/analytics/customers?page=1&page_size=1&sort=risk"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["totalCustomers"] == 3
    assert data["summary"]["customersWithActiveAlerts"] == 1
    assert data["summary"]["activeAccounts"] > 0
    assert data["total"] == 3
    assert data["pageSize"] == 1
    assert len(data["customers"]) == 1
    assert data["customers"][0]["risk"] == "Critical"
    assert data["customers"][0]["activeAlertCount"] == 1

    async with session_factory() as db:
        customer = await db.scalar(
            select(Customer).where(Customer.customer_segment == "HIGH_NET_WORTH")
        )
        email = (await db.get(User, customer.user_id)).email

    response = await admin_client.get(
        f"/api/v1/analytics/customers?q={email}&segment=High%20Value"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["customers"][0]["segment"] == "HIGH_NET_WORTH"

    response = await admin_client.get(
        "/api/v1/analytics/customers?risk=MEDIUM&alerts=none"
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_customer_directory_forbids_customer(client):
    response = await client.get("/api/v1/analytics/customers")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_three_analytics_endpoints_share_customer_risk_level(
    admin_client, session_factory
):
    async with session_factory() as db:
        customer = await db.scalar(select(Customer).order_by(Customer.created_at))
        db.add(
            BehaviourEvent(
                customer_id=customer.id,
                event_type="PAGE_VIEW",
                page="/portal/dashboard",
                action="VIEW",
                session_duration=30,
                event_metadata={},
                timestamp=datetime.now(timezone.utc),
            )
        )
        await db.commit()

    directory = await admin_client.get("/api/v1/analytics/customers?page_size=100")
    overview = await admin_client.get("/api/v1/analytics/overview")
    behaviour = await admin_client.get("/api/v1/analytics/behaviour?page_size=100")

    assert directory.status_code == overview.status_code == behaviour.status_code == 200
    directory_customer = next(
        item
        for item in directory.json()["customers"]
        if item["id"] == str(customer.id)
    )
    overview_customer = next(
        item
        for item in overview.json()["customers"]
        if item["id"] == str(customer.id)
    )
    behaviour_customer = next(
        item
        for item in behaviour.json()["customer_behaviour"]["items"]
        if item["customer_id"] == str(customer.id)
    )
    assert (
        directory_customer["risk"]
        == overview_customer["risk"]
        == behaviour_customer["risk"]
        == "Critical"
    )


@pytest.mark.asyncio
async def test_behaviour_risk_is_null_without_profile(admin_client, session_factory):
    async with session_factory() as db:
        customer = await db.scalar(
            select(Customer)
            .where(
                ~Customer.id.in_(
                    select(CustomerRiskProfile.customer_id)
                )
            )
            .order_by(Customer.created_at.desc())
        )
        db.add(
            BehaviourEvent(
                customer_id=customer.id,
                event_type="PAGE_VIEW",
                page="/portal/dashboard",
                action="VIEW",
                session_duration=30,
                event_metadata={},
                timestamp=datetime.now(timezone.utc),
            )
        )
        await db.commit()

    response = await admin_client.get("/api/v1/analytics/behaviour?page_size=100")
    assert response.status_code == 200
    item = next(
        item
        for item in response.json()["customer_behaviour"]["items"]
        if item["customer_id"] == str(customer.id)
    )
    assert item["risk"] is None
