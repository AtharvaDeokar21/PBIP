import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_db
from app.main import app
from app.models.fraud import FraudAlert, FraudEvent, FraudInvestigation
from app.models.identity import Customer, User
from app.models.system import AuditLog
from app.schemas.fraud import FraudAlertUpdate
from app.services.fraud_service import FraudService
from tests.conftest import GENERATED_PASSWORD


@pytest.fixture
async def admin_client(session_factory, seed):
    """Admin HTTP client that cleans up any role mutation on teardown."""
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

    # Cleanup: restore user role
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        if user:
            user.role = original_role
            await db.commit()

    app.dependency_overrides.clear()


@pytest.fixture
async def fraud_analyst_client(session_factory, seed):
    """Fraud analyst HTTP client that cleans up any role mutation on teardown."""
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

    # Cleanup: restore user role
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        if user:
            user.role = original_role
            await db.commit()

    app.dependency_overrides.clear()


@pytest.fixture
async def seeded_fraud_data(session_factory, seed):
    """Seed sample fraud alerts and events for testing read queries."""
    async with session_factory() as db:
        customer = seed.customer

        event1 = FraudEvent(
            id=uuid.uuid4(),
            customer_id=customer.id,
            transaction_id=None,
            event_type="SCENARIO_1",
            risk_score=Decimal("85.50"),
            severity="HIGH",
            description="Large unusual transfer",
            event_metadata={"fraud_amount": 150000.0},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event1)

        alert1 = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event1.id,
            customer_id=customer.id,
            status="OPEN",
            priority=2,  # High
            assigned_to=seed.user.id,
        )
        db.add(alert1)

        event2 = FraudEvent(
            id=uuid.uuid4(),
            customer_id=customer.id,
            transaction_id=None,
            event_type="SCENARIO_2",
            risk_score=Decimal("95.00"),
            severity="CRITICAL",
            description="Impossible travel login detected",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event2)

        alert2 = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event2.id,
            customer_id=customer.id,
            status="IN_REVIEW",
            priority=1,  # Critical
            assigned_to=None,
        )
        db.add(alert2)

        # Alert 2 has multiple investigation records to test latest selection determinism
        inv2_old = FraudInvestigation(
            id=uuid.uuid4(),
            alert_id=alert2.id,
            analyst_id=seed.user.id,
            notes="Earlier investigation note.",
            action_taken=None,
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        db.add(inv2_old)

        inv2_new = FraudInvestigation(
            id=uuid.uuid4(),
            alert_id=alert2.id,
            analyst_id=seed.user.id,
            notes="Latest investigation note.\nCustomer contacted.",
            action_taken="Account placed on temporary hold",
            started_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
        db.add(inv2_new)

        await db.commit()
        return {
            "alert1": alert1,
            "alert2": alert2,
            "event1": event1,
            "event2": event2,
            "inv2_new": inv2_new,
        }


@pytest.mark.asyncio
async def test_list_investigations_empty(admin_client):
    response = await admin_client.get("/api/v1/fraud/investigations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_investigations_with_data(admin_client, seeded_fraud_data):
    response = await admin_client.get("/api/v1/fraud/investigations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    items = data["items"]
    assert len(items) == 2

    # Check alert with investigation (verifies latest investigation selection)
    item_with_inv = next(i for i in items if i["alertId"] == str(seeded_fraud_data["alert2"].id))
    assert item_with_inv["severity"] == "Critical"
    assert item_with_inv["status"] == "In review"
    assert item_with_inv["type"] == "New sign-in location"
    assert len(item_with_inv["notes"]) == 2
    assert "Latest investigation note." in item_with_inv["notes"]
    assert "Earlier investigation note." not in item_with_inv["notes"]

    # Check alert without investigation
    item_no_inv = next(i for i in items if i["alertId"] == str(seeded_fraud_data["alert1"].id))
    assert item_no_inv["severity"] == "High"
    assert item_no_inv["status"] == "Open"
    assert item_no_inv["type"] == "Unusual transfer amount"
    assert item_no_inv["notes"] == []
    assert item_no_inv["amount"] == 150000.0


@pytest.mark.asyncio
async def test_list_investigations_filter_severity(admin_client, seeded_fraud_data):
    response = await admin_client.get("/api/v1/fraud/investigations", params={"severity": "Critical"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["severity"] == "Critical"


@pytest.mark.asyncio
async def test_list_investigations_filter_status(admin_client, seeded_fraud_data):
    response = await admin_client.get("/api/v1/fraud/investigations", params={"status": "Open"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "Open"


@pytest.mark.asyncio
async def test_list_investigations_filter_assignee(admin_client, seed, seeded_fraud_data):
    # Test unassigned filter
    res_unassigned = await admin_client.get("/api/v1/fraud/investigations", params={"assignee": "Unassigned"})
    assert res_unassigned.status_code == 200
    assert res_unassigned.json()["total"] == 1
    assert res_unassigned.json()["items"][0]["assignedTo"] == "Unassigned"

    # Test assigned email search
    res_assigned = await admin_client.get("/api/v1/fraud/investigations", params={"assignee": seed.user.email})
    assert res_assigned.status_code == 200
    assert res_assigned.json()["total"] == 1
    assert res_assigned.json()["items"][0]["assignedTo"] == seed.user.email


@pytest.mark.asyncio
async def test_list_investigations_search_by_customer_name(admin_client, seed, seeded_fraud_data):
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": seed.customer.first_name},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_investigations_search_by_alert_id(admin_client, seeded_fraud_data):
    alert_id_prefix = str(seeded_fraud_data["alert1"].id)[:8]
    # Test searching by display prefix like "FA-ABC12345"
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": f"FA-{alert_id_prefix}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["alertId"] == str(seeded_fraud_data["alert1"].id)


@pytest.mark.asyncio
async def test_list_investigations_search_by_case_id(admin_client, seeded_fraud_data):
    inv_id_prefix = str(seeded_fraud_data["inv2_new"].id)[:8]
    # Test searching by display prefix like "INV-ABC12345"
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": f"INV-{inv_id_prefix}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["alertId"] == str(seeded_fraud_data["alert2"].id)


@pytest.mark.asyncio
async def test_list_investigations_search_by_description(admin_client, seeded_fraud_data):
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": "Impossible travel"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["alertId"] == str(seeded_fraud_data["alert2"].id)


@pytest.mark.asyncio
async def test_list_investigations_search_by_customer_number(admin_client, seed, seeded_fraud_data):
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": seed.customer.customer_number},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_list_investigations_search_by_event_type(admin_client, seeded_fraud_data):
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": "SCENARIO_1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["alertId"] == str(seeded_fraud_data["alert1"].id)


@pytest.mark.asyncio
async def test_list_investigations_invalid_pagination_params(admin_client):
    # page < 1 should return 422 Unprocessable Entity
    res = await admin_client.get("/api/v1/fraud/investigations", params={"page": 0})
    assert res.status_code == 422

    # page_size > 100 should return 422
    res2 = await admin_client.get("/api/v1/fraud/investigations", params={"page_size": 101})
    assert res2.status_code == 422


@pytest.mark.asyncio
async def test_list_investigations_pagination_and_filter_interaction(admin_client, seeded_fraud_data):
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"page": 1, "page_size": 1, "severity": "Critical"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["severity"] == "Critical"


@pytest.mark.asyncio
async def test_list_investigations_read_only_does_not_mutate_records(admin_client, session_factory, seeded_fraud_data):
    # Capture full snapshots of record values, not just counts
    async with session_factory() as db:
        initial_alert = await db.get(FraudAlert, seeded_fraud_data["alert1"].id)
        assert initial_alert is not None
        initial_status = initial_alert.status
        initial_priority = initial_alert.priority
        initial_updated_at = initial_alert.updated_at
        initial_resolved_at = initial_alert.resolved_at

    response = await admin_client.get("/api/v1/fraud/investigations")
    assert response.status_code == 200

    async with session_factory() as db:
        after_alert = await db.get(FraudAlert, seeded_fraud_data["alert1"].id)
        assert after_alert is not None
        assert after_alert.status == initial_status
        assert after_alert.priority == initial_priority
        assert after_alert.updated_at == initial_updated_at
        assert after_alert.resolved_at == initial_resolved_at


@pytest.mark.asyncio
async def test_list_investigations_fraud_analyst_authorized(fraud_analyst_client, seeded_fraud_data):
    response = await fraud_analyst_client.get("/api/v1/fraud/investigations")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_investigations_customer_forbidden(client, seeded_fraud_data):
    # Customer client from conftest fixture
    response = await client.get("/api/v1/fraud/investigations")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_investigations_unauthenticated():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauth_client:
        response = await unauth_client.get("/api/v1/fraud/investigations")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_investigations_missing_customer_returns_null(admin_client, session_factory, seed):
    """Verify that an alert with an unresolvable or missing customer serializes customerId as null, not 'None'."""
    missing_cust_id = uuid.uuid4()
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=missing_cust_id,
            transaction_id=None,
            event_type="ORPHAN_ALERT_TEST",
            risk_score=Decimal("50.00"),
            severity="MEDIUM",
            description="Alert without customer record in database",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)

        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=missing_cust_id,
            status="OPEN",
            priority=3,
            assigned_to=None,
        )
        db.add(alert)
        await db.commit()
        created_alert_id = str(alert.id)

    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": "ORPHAN_ALERT_TEST"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["alertId"] == created_alert_id
    assert item["customerName"] == "Unknown Customer"
    # Verify customerId is valid string if alert.customer_id is set or None, and NEVER the string "None"
    assert item["customerId"] != "None"


@pytest.mark.asyncio
async def test_list_investigations_search_short_prefixed_ids(admin_client, seeded_fraud_data):
    """Verify searching for short displayed IDs such as INV-0041 or FA-2041 behaves correctly."""
    alert1_id = str(seeded_fraud_data["alert1"].id)
    # Use 4 hex characters from the alert UUID
    short_segment = alert1_id[:4]
    response = await admin_client.get(
        "/api/v1/fraud/investigations",
        params={"search": f"FA-{short_segment}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert any(i["alertId"] == alert1_id for i in data["items"])


# ==============================================================================
# Scope B: Fraud Alert Mutation Tests (PATCH /api/v1/fraud/alerts/{alert_id})
# ==============================================================================


@pytest.mark.asyncio
async def test_patch_alert_unauthenticated(seeded_fraud_data):
    alert_id = seeded_fraud_data["alert1"].id
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as unauth_client:
        response = await unauth_client.patch(
            f"/api/v1/fraud/alerts/{alert_id}",
            json={"status": "IN_REVIEW"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_patch_alert_customer_forbidden(client, seeded_fraud_data):
    alert_id = seeded_fraud_data["alert1"].id
    response = await client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_patch_alert_analyst_authorized(fraud_analyst_client, seeded_fraud_data):
    alert_id = seeded_fraud_data["alert1"].id
    response = await fraud_analyst_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_REVIEW"


@pytest.mark.asyncio
async def test_patch_alert_admin_authorized(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="ADMIN_TEST",
            risk_score=Decimal("70.00"),
            severity="HIGH",
            description="Admin mutation test",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=2,
            assigned_to=None,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "ESCALATED"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ESCALATED"


@pytest.mark.asyncio
async def test_patch_alert_not_found(admin_client):
    random_id = uuid.uuid4()
    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{random_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Fraud alert not found"


@pytest.mark.asyncio
async def test_patch_alert_invalid_status(admin_client, seeded_fraud_data):
    alert_id = seeded_fraud_data["alert1"].id
    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "NOT_A_VALID_STATUS"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_alert_invalid_transition(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="TRANSITION_TEST",
            risk_score=Decimal("60.00"),
            severity="MEDIUM",
            description="Testing invalid transitions",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=3,
            assigned_to=None,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    # OPEN -> RESOLVED is disallowed
    res_resolve = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "RESOLVED"},
    )
    assert res_resolve.status_code == 422
    assert "cannot transition" in res_resolve.json()["detail"]

    # OPEN -> FALSE_POSITIVE is disallowed
    res_fp = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "FALSE_POSITIVE"},
    )
    assert res_fp.status_code == 422
    assert "cannot transition" in res_fp.json()["detail"]

    # OPEN -> OPEN (no-op) is disallowed
    res_noop = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "OPEN"},
    )
    assert res_noop.status_code == 422
    assert "already in status" in res_noop.json()["detail"]


@pytest.mark.asyncio
async def test_patch_alert_open_to_in_review_and_auto_assignment(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="ASSIGN_TEST_1",
            risk_score=Decimal("80.00"),
            severity="HIGH",
            description="Auto assign on in_review",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=2,
            assigned_to=None,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_REVIEW"
    assert data["assigned_to"] == str(seed.user.id)
    assert data["resolved_at"] is None


@pytest.mark.asyncio
async def test_patch_alert_open_to_escalated_and_auto_assignment(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="ASSIGN_TEST_2",
            risk_score=Decimal("90.00"),
            severity="CRITICAL",
            description="Auto assign on escalate",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=1,
            assigned_to=None,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "ESCALATED"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ESCALATED"
    assert data["assigned_to"] == str(seed.user.id)
    assert data["resolved_at"] is None


@pytest.mark.asyncio
async def test_patch_alert_in_review_to_escalated(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="IN_REV_TO_ESC",
            risk_score=Decimal("88.00"),
            severity="HIGH",
            description="In review to escalated",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="IN_REVIEW",
            priority=2,
            assigned_to=seed.user.id,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "ESCALATED"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ESCALATED"


@pytest.mark.asyncio
async def test_patch_alert_escalated_to_in_review(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="ESC_TO_IN_REV",
            risk_score=Decimal("82.00"),
            severity="HIGH",
            description="Escalated to in review",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="ESCALATED",
            priority=2,
            assigned_to=seed.user.id,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "In review"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_REVIEW"


@pytest.mark.asyncio
async def test_patch_alert_in_review_to_resolved_sets_timestamp(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="RESOLVE_TEST",
            risk_score=Decimal("75.00"),
            severity="MEDIUM",
            description="Resolving alert",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="IN_REVIEW",
            priority=3,
            assigned_to=seed.user.id,
            resolved_at=None,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "RESOLVED", "resolution_notes": "Customer confirmed legitimate."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_at"] is not None
    assert data["resolution_notes"] == "Customer confirmed legitimate."


@pytest.mark.asyncio
async def test_patch_alert_escalated_to_false_positive_sets_timestamp(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="FP_TEST",
            risk_score=Decimal("65.00"),
            severity="MEDIUM",
            description="Marking false positive",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="ESCALATED",
            priority=2,
            assigned_to=seed.user.id,
            resolved_at=None,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "False positive"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FALSE_POSITIVE"
    assert data["resolved_at"] is not None


@pytest.mark.asyncio
async def test_patch_alert_reopening_resolved_to_in_review_clears_resolved_at(admin_client, session_factory, seed):
    past_time = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="REOPEN_RES_TEST",
            risk_score=Decimal("80.00"),
            severity="HIGH",
            description="Reopening resolved",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="RESOLVED",
            priority=2,
            assigned_to=seed.user.id,
            resolved_at=past_time,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_REVIEW"
    assert data["resolved_at"] is None


@pytest.mark.asyncio
async def test_patch_alert_reopening_false_positive_to_in_review_clears_resolved_at(admin_client, session_factory, seed):
    past_time = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="REOPEN_FP_TEST",
            risk_score=Decimal("80.00"),
            severity="HIGH",
            description="Reopening FP",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="FALSE_POSITIVE",
            priority=2,
            assigned_to=seed.user.id,
            resolved_at=past_time,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_REVIEW"
    assert data["resolved_at"] is None


@pytest.mark.asyncio
async def test_patch_alert_preserves_existing_assignment(fraud_analyst_client, session_factory, seed):
    existing_assignee_id = uuid.uuid4()
    async with session_factory() as db:
        other_user = User(
            id=existing_assignee_id,
            email="existing.analyst@bank.com",
            role="FRAUD_ANALYST",
            password_hash="pw",
            is_active=True,
        )
        db.add(other_user)
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="PRESERVE_ASSIGN_TEST",
            risk_score=Decimal("80.00"),
            severity="HIGH",
            description="Preserve assignment",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=2,
            assigned_to=existing_assignee_id,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await fraud_analyst_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 200
    assert response.json()["assigned_to"] == str(existing_assignee_id)


@pytest.mark.asyncio
async def test_patch_alert_preserves_existing_resolution_notes_when_omitted(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="PRESERVE_NOTES_TEST",
            risk_score=Decimal("70.00"),
            severity="MEDIUM",
            description="Preserve notes",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=3,
            assigned_to=seed.user.id,
            resolution_notes="Crucial historical note that must not be lost.",
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 200
    assert response.json()["resolution_notes"] == "Crucial historical note that must not be lost."


@pytest.mark.asyncio
async def test_patch_alert_creates_audit_log(admin_client, session_factory, seed):
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="AUDIT_TEST",
            risk_score=Decimal("85.00"),
            severity="HIGH",
            description="Testing audit log generation",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=uuid.uuid4(),
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=2,
            assigned_to=None,
        )
        db.add(alert)
        await db.commit()
        alert_id = alert.id

    response = await admin_client.patch(
        f"/api/v1/fraud/alerts/{alert_id}",
        json={"status": "IN_REVIEW"},
    )
    assert response.status_code == 200

    async with session_factory() as db:
        audit = await db.scalar(
            select(AuditLog).where(
                AuditLog.entity_id == alert_id,
                AuditLog.action == "FRAUD_ALERT_STATUS_UPDATED",
            )
        )
        assert audit is not None
        assert audit.entity_type == "FRAUD_ALERT"
        assert audit.user_id == seed.user.id
        assert audit.old_value["status"] == "OPEN"
        assert audit.old_value["assigned_to"] is None
        assert audit.new_value["status"] == "IN_REVIEW"
        assert audit.new_value["assigned_to"] == str(seed.user.id)
        assert audit.created_at is not None


@pytest.mark.asyncio
async def test_patch_alert_rollback_on_failure(session_factory, seed):
    alert_id = uuid.uuid4()
    async with session_factory() as db:
        event = FraudEvent(
            id=uuid.uuid4(),
            customer_id=seed.customer.id,
            transaction_id=None,
            event_type="ROLLBACK_TEST",
            risk_score=Decimal("90.00"),
            severity="CRITICAL",
            description="Testing failure rollback",
            event_metadata={},
            detected_at=datetime.now(timezone.utc),
        )
        db.add(event)
        alert = FraudAlert(
            id=alert_id,
            fraud_event_id=event.id,
            customer_id=seed.customer.id,
            status="OPEN",
            priority=1,
            assigned_to=None,
        )
        db.add(alert)
        await db.commit()

    async with session_factory() as db:
        service = FraudService(db)
        payload = FraudAlertUpdate(status="IN_REVIEW")

        async def failing_commit():
            raise RuntimeError("Simulated DB write failure")

        db.commit = failing_commit

        with pytest.raises(RuntimeError, match="Simulated DB write failure"):
            await service.update_alert_status(
                alert_id=alert_id,
                payload=payload,
                acting_user=seed.user,
            )

    async with session_factory() as db:
        fresh_alert = await db.get(FraudAlert, alert_id)
        assert fresh_alert.status == "OPEN"
        assert fresh_alert.assigned_to is None

        audit = await db.scalar(
            select(AuditLog).where(
                AuditLog.entity_id == alert_id,
                AuditLog.action == "FRAUD_ALERT_STATUS_UPDATED",
            )
        )
        assert audit is None


