import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.main import app
from app.models.identity import Customer, User
from app.models.system import AuditLog
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
async def test_audit_logs_unauthenticated_returns_401():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/compliance/audit-logs")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_audit_logs_customer_forbidden_returns_403(customer_client):
    response = await customer_client.get("/api/v1/compliance/audit-logs")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_compliance_officer_returns_200(compliance_officer_client):
    response = await compliance_officer_client.get("/api/v1/compliance/audit-logs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_audit_logs_admin_returns_200(admin_client):
    response = await admin_client.get("/api/v1/compliance/audit-logs")
    assert response.status_code == 200


# ===========================================================================
# 2. Data Retrieval, Field Mapping, and Security Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_audit_logs_retrieves_real_persisted_audit_records(session_factory, seed, compliance_officer_client):
    """Persisted AuditLog rows are retrieved with correctly mapped fields."""
    now = datetime.now(timezone.utc)
    audit_id = uuid.uuid4()
    async with session_factory() as db:
        log = AuditLog(
            id=audit_id,
            user_id=seed.user.id,
            action="CUSTOMER_PROFILE_UPDATED",
            entity_type="CUSTOMER",
            entity_id=seed.customer.id,
            old_value={"phone": "9999999999"},
            new_value={"phone": "8888888888"},
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0",
            created_at=now,
        )
        db.add(log)
        await db.commit()

    response = await compliance_officer_client.get("/api/v1/compliance/audit-logs")
    assert response.status_code == 200
    data = response.json()

    matching = next((item for item in data["items"] if item["id"] == f"AL-{str(audit_id).upper()}"), None)
    assert matching is not None
    assert matching["actor"] == f"{seed.customer.first_name} {seed.customer.last_name}"
    assert matching["actorRole"] == "Customer"
    assert matching["action"] == "Profile update"
    assert matching["resource"] == "Customer Profile"
    assert matching["resourceId"] == str(seed.customer.id)
    assert matching["outcome"] == "Success"
    assert matching["ipAddress"] == "192.168.1.100"
    assert matching["customerId"] == str(seed.customer.id)


@pytest.mark.asyncio
async def test_audit_logs_does_not_expose_raw_json_values(session_factory, seed, compliance_officer_client):
    """The API response must not expose raw old_value or new_value payload dicts."""
    async with session_factory() as db:
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=seed.user.id,
            action="CUSTOMER_PROFILE_UPDATED",
            entity_type="CUSTOMER",
            entity_id=seed.customer.id,
            old_value={"sensitive_internal_key": "secret_old"},
            new_value={"sensitive_internal_key": "secret_new"},
            ip_address="10.0.0.1",
            user_agent="TestAgent/1.0",
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        await db.commit()

    response = await compliance_officer_client.get("/api/v1/compliance/audit-logs")
    assert response.status_code == 200
    data = response.json()

    for item in data["items"]:
        assert "oldValue" not in item
        assert "newValue" not in item
        assert "old_value" not in item
        assert "new_value" not in item


@pytest.mark.asyncio
async def test_audit_logs_unknown_action_code_handled_safely(session_factory, seed, compliance_officer_client):
    """Unknown action codes are rendered cleanly without throwing errors."""
    audit_id = uuid.uuid4()
    async with session_factory() as db:
        log = AuditLog(
            id=audit_id,
            user_id=seed.user.id,
            action="CUSTOM_UNKNOWN_SECURITY_OP",
            entity_type="CUSTOM_ENTITY",
            entity_id=uuid.uuid4(),
            ip_address="127.0.0.1",
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        await db.commit()

    response = await compliance_officer_client.get(f"/api/v1/compliance/audit-logs?search=AL-{str(audit_id).upper()}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["action"] == "Custom unknown security op"
    assert data["items"][0]["resource"] == "Custom Entity"


# ===========================================================================
# 3. Filtering, Search, Ordering, and Pagination Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_audit_logs_filter_by_action(session_factory, seed, compliance_officer_client):
    """Action filter correctly matches both canonical action and display label."""
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    async with session_factory() as db:
        log1 = AuditLog(
            id=id1,
            user_id=seed.user.id,
            action="TRANSFER_CREATED",
            created_at=datetime.now(timezone.utc),
        )
        log2 = AuditLog(
            id=id2,
            user_id=seed.user.id,
            action="USER_LOGIN",
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([log1, log2])
        await db.commit()

    # Query with display label "Transfer created"
    res1 = await compliance_officer_client.get("/api/v1/compliance/audit-logs?action=Transfer created")
    assert res1.status_code == 200
    ids1 = [item["id"] for item in res1.json()["items"]]
    assert f"AL-{str(id1).upper()}" in ids1
    assert f"AL-{str(id2).upper()}" not in ids1

    # Query with canonical action "TRANSFER_CREATED"
    res2 = await compliance_officer_client.get("/api/v1/compliance/audit-logs?action=TRANSFER_CREATED")
    assert res2.status_code == 200
    ids2 = [item["id"] for item in res2.json()["items"]]
    assert f"AL-{str(id1).upper()}" in ids2


@pytest.mark.asyncio
async def test_audit_logs_filter_by_actor(session_factory, seed, compliance_officer_client):
    """Actor filter correctly matches customer name or user email."""
    # Create another distinct user
    other_user = User(
        id=uuid.uuid4(),
        email="other.officer@bank.com",
        password_hash="dummy",
        role="OFFICER",
    )
    log_other = AuditLog(
        id=uuid.uuid4(),
        user_id=other_user.id,
        action="USER_LOGIN",
        created_at=datetime.now(timezone.utc),
    )
    async with session_factory() as db:
        db.add_all([other_user, log_other])
        await db.commit()

    res = await compliance_officer_client.get(f"/api/v1/compliance/audit-logs?actor={other_user.email}")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert all(other_user.email in item["actor"] for item in data["items"])


@pytest.mark.asyncio
async def test_audit_logs_search(session_factory, seed, compliance_officer_client):
    """Search matches by Log ID prefix, actor name, or action."""
    target_id = uuid.uuid4()
    async with session_factory() as db:
        log = AuditLog(
            id=target_id,
            user_id=seed.user.id,
            action="SPECIAL_SEARCH_ACTION",
            ip_address="172.16.50.25",
            created_at=datetime.now(timezone.utc),
        )
        db.add(log)
        await db.commit()

    # Search by full formatted ID
    res_id = await compliance_officer_client.get(f"/api/v1/compliance/audit-logs?search=AL-{str(target_id).upper()}")
    assert res_id.status_code == 200
    assert res_id.json()["total"] == 1
    assert res_id.json()["items"][0]["id"] == f"AL-{str(target_id).upper()}"

    # Search by IP
    res_ip = await compliance_officer_client.get("/api/v1/compliance/audit-logs?search=172.16.50.25")
    assert res_ip.status_code == 200
    assert any(item["id"] == f"AL-{str(target_id).upper()}" for item in res_ip.json()["items"])


@pytest.mark.asyncio
async def test_audit_logs_outcome_filtering(compliance_officer_client):
    """Filtering by Failure or Warning returns 0 items truthfully since audit_logs records successful actions."""
    res_fail = await compliance_officer_client.get("/api/v1/compliance/audit-logs?outcome=Failure")
    assert res_fail.status_code == 200
    assert res_fail.json()["total"] == 0
    assert res_fail.json()["items"] == []

    res_warn = await compliance_officer_client.get("/api/v1/compliance/audit-logs?outcome=Warning")
    assert res_warn.status_code == 200
    assert res_warn.json()["total"] == 0


@pytest.mark.asyncio
async def test_audit_logs_pagination_and_deterministic_order(session_factory, seed, compliance_officer_client):
    """Pagination respects limit and offset, and sorts newest first with secondary id DESC tie-break."""
    fixed_time = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)
    id_a = uuid.UUID("a0000000-0000-0000-0000-000000000001")
    id_b = uuid.UUID("b0000000-0000-0000-0000-000000000002")

    async with session_factory() as db:
        # Same timestamp, different UUIDs
        log1 = AuditLog(id=id_a, user_id=seed.user.id, action="DETERMINISTIC_ORDER_A", created_at=fixed_time)
        log2 = AuditLog(id=id_b, user_id=seed.user.id, action="DETERMINISTIC_ORDER_B", created_at=fixed_time)
        db.add_all([log1, log2])
        await db.commit()

    # Query page 1 with page_size = 1 and search for these specific logs
    res_p1 = await compliance_officer_client.get(
        "/api/v1/compliance/audit-logs?page=1&page_size=1&search=DETERMINISTIC_ORDER"
    )
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()
    assert data_p1["total"] == 2
    assert len(data_p1["items"]) == 1
    # Secondary sort id DESC -> id_b comes first
    assert data_p1["items"][0]["id"] == f"AL-{str(id_b).upper()}"

    # Page 2 -> id_a
    res_p2 = await compliance_officer_client.get(
        "/api/v1/compliance/audit-logs?page=2&page_size=1&search=DETERMINISTIC_ORDER"
    )
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert len(data_p2["items"]) == 1
    assert data_p2["items"][0]["id"] == f"AL-{str(id_a).upper()}"


@pytest.mark.asyncio
async def test_audit_logs_summary_counts_accuracy(session_factory, seed, compliance_officer_client):
    """Summary reflects total count across the dataset, not merely current page size."""
    async with session_factory() as db:
        logs = [
            AuditLog(
                id=uuid.uuid4(),
                user_id=seed.user.id,
                action="SUMMARY_ACTION_TEST",
                created_at=datetime.now(timezone.utc),
            )
            for _ in range(5)
        ]
        db.add_all(logs)
        await db.commit()

    res = await compliance_officer_client.get(
        "/api/v1/compliance/audit-logs?search=SUMMARY_ACTION_TEST&page=1&page_size=2"
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["summary"]["totalEvents"] == 5
    assert data["summary"]["successCount"] == 5
    assert data["summary"]["failureCount"] == 0
    assert data["summary"]["warningCount"] == 0


@pytest.mark.asyncio
async def test_audit_logs_invalid_pagination_parameters(compliance_officer_client):
    """Invalid page (<1) or page_size (>100 or <1) returns HTTP 422."""
    res_page0 = await compliance_officer_client.get("/api/v1/compliance/audit-logs?page=0")
    assert res_page0.status_code == 422

    res_page_over = await compliance_officer_client.get("/api/v1/compliance/audit-logs?page_size=101")
    assert res_page_over.status_code == 422


# ===========================================================================
# 4. Multi-Page Export & Batching Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_audit_logs_normal_pagination_remains_intact(session_factory, seed, compliance_officer_client):
    """Table pagination displays exact page size slice (15) and total count (40)."""
    async with session_factory() as db:
        logs = [
            AuditLog(
                id=uuid.uuid4(),
                user_id=seed.user.id,
                action="PAGINATION_VERIFY_ACTION",
                created_at=datetime.now(timezone.utc),
            )
            for _ in range(40)
        ]
        db.add_all(logs)
        await db.commit()

    # Request standard page 1 with page_size=15
    res = await compliance_officer_client.get(
        "/api/v1/compliance/audit-logs?search=PAGINATION_VERIFY_ACTION&page=1&page_size=15"
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 15
    assert data["total"] == 40
    assert data["page"] == 1
    assert data["pageSize"] == 15


@pytest.mark.asyncio
async def test_audit_logs_export_all_records_across_pages_without_filters(session_factory, seed, compliance_officer_client):
    """Exporting with bounded batches fetches all 40 records, not just the first 15."""
    async with session_factory() as db:
        logs = [
            AuditLog(
                id=uuid.uuid4(),
                user_id=seed.user.id,
                action="EXPORT_ALL_ACTION",
                created_at=datetime.now(timezone.utc),
            )
            for _ in range(40)
        ]
        db.add_all(logs)
        await db.commit()

    # Simulate client export bounded batch retrieval with page_size=100
    res_batch = await compliance_officer_client.get(
        "/api/v1/compliance/audit-logs?search=EXPORT_ALL_ACTION&page=1&page_size=100"
    )
    assert res_batch.status_code == 200
    data = res_batch.json()
    assert data["total"] == 40
    # All 40 records retrieved, far exceeding the 15-row page slice
    assert len(data["items"]) == 40
    unique_ids = {item["id"] for item in data["items"]}
    assert len(unique_ids) == 40


@pytest.mark.asyncio
async def test_audit_logs_export_with_filters_across_pages(session_factory, seed, compliance_officer_client):
    """Filtered export retrieves all matching records across multiple pages without duplicates."""
    # Seed 25 matching records and 15 non-matching records (total 40)
    async with session_factory() as db:
        matching_logs = [
            AuditLog(
                id=uuid.uuid4(),
                user_id=seed.user.id,
                action="TARGET_EXPORT_ACTION",
                created_at=datetime.now(timezone.utc),
            )
            for _ in range(25)
        ]
        other_logs = [
            AuditLog(
                id=uuid.uuid4(),
                user_id=seed.user.id,
                action="OTHER_EXPORT_ACTION",
                created_at=datetime.now(timezone.utc),
            )
            for _ in range(15)
        ]
        db.add_all(matching_logs + other_logs)
        await db.commit()

    # Multi-page batch loop simulating client exportAllAuditLogs with batch_size=10
    batch_size = 10
    page = 1
    collected_items = []
    seen_ids = set()

    while True:
        res = await compliance_officer_client.get(
            f"/api/v1/compliance/audit-logs?action=TARGET_EXPORT_ACTION&page={page}&page_size={batch_size}"
        )
        assert res.status_code == 200
        data = res.json()
        items = data["items"]
        if not items:
            break

        for item in items:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                collected_items.append(item)

        if len(collected_items) >= data["total"] or len(items) < batch_size:
            break
        page += 1

    # Exact 25 records matching filter collected across 3 pages (10, 10, 5)
    assert len(collected_items) == 25
    assert len(seen_ids) == 25
    assert all("Target export action" in item["action"] or "TARGET_EXPORT_ACTION" in item["action"] for item in collected_items)

