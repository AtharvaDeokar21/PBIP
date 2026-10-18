import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.database import get_db
from app.main import app
from app.models.banking import Transaction
from app.models.identity import Customer, User
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
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": seed.user.email, "password": GENERATED_PASSWORD},
        )
        assert response.status_code == 200
        client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_overview_total_customers_matches_database(admin_client, session_factory):
    async with session_factory() as db:
        expected = await db.scalar(select(func.count()).select_from(Customer))

    response = await admin_client.get("/api/v1/analytics/overview")

    assert response.status_code == 200
    assert response.json()["summary"]["totalCustomers"] == expected
    assert len(response.json()["customers"]) == expected


@pytest.mark.asyncio
async def test_overview_empty_optional_tables_returns_empty_sections(admin_client):
    response = await admin_client.get("/api/v1/analytics/overview")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["activeFraudAlerts"] == 0
    assert data["summary"]["highRiskCustomers"] == 0
    assert data["summary"]["openInvestigations"] == 0
    assert data["summary"]["complianceAlerts"] == 0
    assert data["alerts"] == []
    assert data["sessions"] == []
    assert data["activity"] == []


@pytest.mark.asyncio
async def test_overview_forbids_customer(client):
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_overview_compliance_alerts_reflects_open_derived_alerts(admin_client, seed, session_factory):
    """Overview summary complianceAlerts accurately reflects open derived compliance alerts."""
    async with session_factory() as db:
        # Eligible transaction: 1,200,000 COMPLETED triggers Rule 1
        txn1 = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-COMPL-OV-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("1200000.00"),
            currency="INR",
            transaction_status="COMPLETED",
            transaction_date=datetime.now(timezone.utc),
        )
        # Ineligible transaction: 1,500,000 but PENDING (does not trigger alert)
        txn2 = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-COMPL-OV-PEND-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("1500000.00"),
            currency="INR",
            transaction_status="PENDING",
            transaction_date=datetime.now(timezone.utc),
        )
        db.add_all([txn1, txn2])
        await db.commit()

    response = await admin_client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["complianceAlerts"] >= 1
