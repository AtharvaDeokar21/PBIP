import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from app.models.identity import Customer, User
from app.models.system import SecurityEvent
from tests.conftest import GENERATED_PASSWORD


@pytest.fixture
async def compliance_officer_client(session_factory, seed):
    """Compliance Officer HTTP client that restores user role on teardown."""
    async def _get_test_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    original_role = seed.user.role
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        user.role = "COMPLIANCE_OFFICER"
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

    # Teardown
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        if user:
            user.role = original_role
            await db.commit()

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_client(session_factory, seed):
    """Admin HTTP client that restores user role on teardown."""
    async def _get_test_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    original_role = seed.user.role
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

    # Teardown
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        if user:
            user.role = original_role
            await db.commit()

    app.dependency_overrides.clear()


@pytest.fixture
async def fraud_analyst_client(session_factory, seed):
    """Fraud Analyst HTTP client that restores user role on teardown."""
    async def _get_test_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    original_role = seed.user.role
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        user.role = "FRAUD_ANALYST"
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

    # Teardown
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        if user:
            user.role = original_role
            await db.commit()

    app.dependency_overrides.clear()


@pytest.fixture
async def customer_client(session_factory, seed):
    """Customer role HTTP client."""
    async def _get_test_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
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


# ===========================================================================
# 1. Authentication and Authorization Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_security_events_unauthenticated_returns_401():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/compliance/security-events")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_security_events_customer_forbidden_returns_403(customer_client):
    response = await customer_client.get("/api/v1/compliance/security-events")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_security_events_admin_returns_200(admin_client):
    response = await admin_client.get("/api/v1/compliance/security-events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_security_events_compliance_officer_returns_200(compliance_officer_client):
    response = await compliance_officer_client.get("/api/v1/compliance/security-events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_security_events_fraud_analyst_returns_200(fraud_analyst_client):
    response = await fraud_analyst_client.get("/api/v1/compliance/security-events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "summary" in data


# ===========================================================================
# 2. Record Retrieval & Schema Structure Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_security_events_structure_and_types(admin_client):
    response = await admin_client.get("/api/v1/compliance/security-events?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["pageSize"], int)
    assert isinstance(data["items"], list)
    assert isinstance(data["summary"], dict)

    summary = data["summary"]
    assert "totalEvents" in summary
    assert "criticalCount" in summary
    assert "requiresReviewCount" in summary
    assert "loggedCount" in summary
    assert "openCount" in summary
    assert "resolvedCount" in summary
    assert "severityCounts" in summary
    assert "channelCounts" in summary

    # Verify severityCounts has standard categories
    for cat in ("Critical", "High", "Medium", "Low"):
        assert cat in summary["severityCounts"]

    # Verify channelCounts has standard categories
    for chan in ("Mobile app", "Net banking", "ATM", "API"):
        assert chan in summary["channelCounts"]

    if data["items"]:
        item = data["items"][0]
        assert "id" in item
        assert item["id"].startswith("SE-")
        assert "customerName" in item
        assert "eventType" in item
        assert "channel" in item
        assert "severity" in item
        assert "status" in item
        assert "detectedAt" in item
        assert "description" in item
        assert "location" in item
        assert "device" in item
        assert "ipAddress" in item


# ===========================================================================
# 3. Pagination and Ordering Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_security_events_pagination_limits(admin_client):
    # Valid pagination
    res_1 = await admin_client.get("/api/v1/compliance/security-events?page=1&page_size=5")
    assert res_1.status_code == 200
    d_1 = res_1.json()
    assert len(d_1["items"]) <= 5

    # Invalid page number (< 1)
    res_invalid_page = await admin_client.get("/api/v1/compliance/security-events?page=0")
    assert res_invalid_page.status_code == 422

    # Invalid page size (> 100)
    res_invalid_size = await admin_client.get("/api/v1/compliance/security-events?page_size=101")
    assert res_invalid_size.status_code == 422


@pytest.mark.asyncio
async def test_security_events_deterministic_ordering(admin_client):
    res = await admin_client.get("/api/v1/compliance/security-events?page=1&page_size=30")
    assert res.status_code == 200
    items = res.json()["items"]

    if len(items) >= 2:
        for i in range(len(items) - 1):
            dt_curr = items[i]["detectedAt"]
            dt_next = items[i + 1]["detectedAt"]
            assert dt_curr >= dt_next


# ===========================================================================
# 4. Search and Filter Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_security_events_search_by_id(admin_client):
    res = await admin_client.get("/api/v1/compliance/security-events?page=1&page_size=1")
    assert res.status_code == 200
    items = res.json()["items"]
    if items:
        target_id = items[0]["id"]
        search_res = await admin_client.get(f"/api/v1/compliance/security-events?search={target_id}")
        assert search_res.status_code == 200
        search_items = search_res.json()["items"]
        assert any(item["id"] == target_id for item in search_items)


@pytest.mark.asyncio
async def test_security_events_search_by_event_type(admin_client):
    res = await admin_client.get("/api/v1/compliance/security-events?search=login")
    assert res.status_code == 200
    items = res.json()["items"]
    for item in items:
        # Should match either type, description, or user/customer
        searchable_text = f"{item['eventType']} {item['description']} {item['customerName']}".lower()
        assert "login" in searchable_text


@pytest.mark.asyncio
async def test_security_events_filter_by_severity(admin_client):
    # Low / Info filter
    res_low = await admin_client.get("/api/v1/compliance/security-events?severity=Low")
    assert res_low.status_code == 200
    for item in res_low.json()["items"]:
        assert item["severity"] == "Low"

    # Medium / Warning filter
    res_med = await admin_client.get("/api/v1/compliance/security-events?severity=Medium")
    assert res_med.status_code == 200
    for item in res_med.json()["items"]:
        assert item["severity"] == "Medium"


@pytest.mark.asyncio
async def test_security_events_filter_by_status(admin_client):
    res_logged = await admin_client.get("/api/v1/compliance/security-events?status=Logged")
    assert res_logged.status_code == 200
    for item in res_logged.json()["items"]:
        assert item["status"] == "Logged"

    res_review = await admin_client.get("/api/v1/compliance/security-events?status=Requires+review")
    assert res_review.status_code == 200
    for item in res_review.json()["items"]:
        assert item["status"] == "Requires review"


@pytest.mark.asyncio
async def test_security_events_filter_by_channel(admin_client):
    res_api = await admin_client.get("/api/v1/compliance/security-events?channel=API")
    assert res_api.status_code == 200
    for item in res_api.json()["items"]:
        assert item["channel"] == "API"

    res_net = await admin_client.get("/api/v1/compliance/security-events?channel=Net+banking")
    assert res_net.status_code == 200
    for item in res_net.json()["items"]:
        assert item["channel"] == "Net banking"


@pytest.mark.asyncio
async def test_security_events_empty_search_returns_zero(admin_client):
    res = await admin_client.get("/api/v1/compliance/security-events?search=NONEXISTENT_SECURITY_TOKEN_XYZ_123")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert data["summary"]["totalEvents"] == 0
