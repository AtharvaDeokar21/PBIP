from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_db
from app.main import app
from app.models.fraud import FraudAlert, FraudEvent
from app.models.identity import Customer, User
from app.models.intelligence import CustomerRiskProfile
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
    assert data["customers"][0]["risk"] == "CRITICAL"
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
