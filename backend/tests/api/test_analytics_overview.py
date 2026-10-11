import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.database import get_db
from app.main import app
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
