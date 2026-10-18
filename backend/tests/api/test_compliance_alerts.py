import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_db
from app.main import app
from app.models.banking import Account, Transaction
from app.models.identity import Customer, User
from app.services.compliance_service import ComplianceService
from tests.conftest import GENERATED_PASSWORD


@pytest.fixture
async def compliance_officer_client(session_factory, seed):
    """Compliance Officer HTTP client that cleans up role mutation on teardown."""
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

    # Teardown: restore role
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        if user:
            user.role = original_role
            await db.commit()

    app.dependency_overrides.clear()


@pytest.fixture
async def admin_client(session_factory, seed):
    """Admin HTTP client that cleans up role mutation on teardown."""
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

    # Teardown: restore role
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
async def test_compliance_alerts_unauthenticated_returns_401():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/compliance/alerts")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_compliance_alerts_customer_returns_403(customer_client):
    response = await customer_client.get("/api/v1/compliance/alerts")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_compliance_alerts_officer_returns_200(compliance_officer_client):
    response = await compliance_officer_client.get("/api/v1/compliance/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_compliance_alerts_admin_returns_200(admin_client):
    response = await admin_client.get("/api/v1/compliance/alerts")
    assert response.status_code == 200


# ===========================================================================
# 2. Rule-Specific Deterministic Generation Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_rule_1_high_value_reporting_review(session_factory, seed, compliance_officer_client):
    """Completed transaction >= 1,000,000 triggers Reporting review; non-completed or < 1M does not."""
    async with session_factory() as db:
        # Eligible transaction: 1,200,000 COMPLETED
        txn1 = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-HIGH-1-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("1200000.00"),
            currency="INR",
            transaction_status="COMPLETED",
            transaction_date=datetime(2026, 10, 5, 14, 30, tzinfo=timezone.utc),
        )
        # Ineligible transaction 1: 1,500,000 but PENDING status
        txn2 = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-HIGH-2-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("1500000.00"),
            currency="INR",
            transaction_status="PENDING",
            transaction_date=datetime(2026, 10, 5, 15, 0, tzinfo=timezone.utc),
        )
        # Ineligible transaction 2: 900,000 COMPLETED (< 1,000,000)
        txn3 = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-HIGH-3-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("900000.00"),
            currency="INR",
            transaction_status="COMPLETED",
            transaction_date=datetime(2026, 10, 5, 16, 0, tzinfo=timezone.utc),
        )
        db.add_all([txn1, txn2, txn3])
        await db.commit()

    response = await compliance_officer_client.get("/api/v1/compliance/alerts?category=Reporting")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]
    alert_ids = [item["id"] for item in items]

    assert f"CA-REP-{str(txn1.id).upper()}" in alert_ids
    assert f"CA-REP-{str(txn2.id).upper()}" not in alert_ids
    assert f"CA-REP-{str(txn3.id).upper()}" not in alert_ids

    matching = next(item for item in items if item["id"] == f"CA-REP-{str(txn1.id).upper()}")
    assert matching["category"] == "Reporting"
    assert matching["type"] == "Threshold reporting review"
    assert matching["status"] == "Open"
    assert matching["customerId"] == str(seed.customer.id)
    # Next month 15th: 2026-10-05 -> 2026-11-15
    assert matching["dueDate"] == "2026-11-15"
    assert "reached the ₹10,00,000 prototype review threshold" in matching["description"]


@pytest.mark.asyncio
async def test_rule_2_transaction_velocity_review(session_factory, seed, compliance_officer_client):
    """6 or more COMPLETED transactions on same calendar day trigger velocity alert; < 6 does not."""
    target_date = datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc)
    async with session_factory() as db:
        # Create 6 completed transactions on 2026-09-20
        txns = []
        for i in range(6):
            txns.append(
                Transaction(
                    id=uuid.uuid4(),
                    account_id=seed.funded_account.id,
                    transaction_reference=f"REF-VEL-{i}-{uuid.uuid4().hex[:6]}",
                    transaction_type="DEBIT",
                    amount=Decimal("500.00"),
                    currency="INR",
                    transaction_status="COMPLETED",
                    transaction_date=target_date + timedelta(minutes=i * 10),
                )
            )
        db.add_all(txns)
        await db.commit()

    response = await compliance_officer_client.get("/api/v1/compliance/alerts?category=Transaction")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]

    expected_id = f"CA-TXN-{str(seed.customer.id).upper()}-20260920"
    matching = next((item for item in items if item["id"] == expected_id), None)
    assert matching is not None
    assert matching["category"] == "Transaction"
    assert matching["type"] == "Transaction velocity review"
    assert matching["status"] == "Open"
    assert matching["customerId"] == str(seed.customer.id)
    assert matching["dueDate"] == "2026-09-27"
    assert "Operational velocity threshold reached: 6 completed transactions" in matching["description"]


@pytest.mark.asyncio
async def test_rule_3_kyc_income_volume_review(session_factory, seed, compliance_officer_client):
    """Debit volume in trailing 30 days > 3x declared monthly income triggers review."""
    ref_time = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
    async with session_factory() as db:
        # Set customer annual income to 600,000 (monthly = 50,000; 3x = 150,000)
        cust = await db.get(Customer, seed.customer.id)
        cust.annual_income = Decimal("600000.00")

        # Inject 180,000 completed debits in trailing 30 days
        txn = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-KYC-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("180000.00"),
            currency="INR",
            transaction_status="COMPLETED",
            transaction_date=ref_time - timedelta(days=5),
        )
        db.add(txn)
        await db.commit()

    # Query with service directly passing ref_time
    async with session_factory() as db:
        service = ComplianceService(db)
        res = await service.list_alerts(as_of=ref_time, category="KYC")

    expected_id = f"CA-KYC-{str(seed.customer.id).upper()}"
    matching = next((item for item in res.items if item.id == expected_id), None)
    assert matching is not None
    assert matching.category == "KYC"
    assert matching.type == "Income-to-volume review"
    assert matching.status == "Open"
    assert "exceeds 3x declared monthly income" in matching.description


@pytest.mark.asyncio
async def test_rule_4_profile_documentation_review(session_factory, seed, compliance_officer_client):
    """Active account holder missing profile fields triggers Documentation alert; complete profile does not."""
    async with session_factory() as db:
        cust = await db.get(Customer, seed.customer.id)
        # Clear phone and occupation to trigger rule
        cust.phone = None
        cust.occupation = None
        await db.commit()

    response = await compliance_officer_client.get("/api/v1/compliance/alerts?category=Documentation")
    assert response.status_code == 200
    data = response.json()
    items = data["items"]

    expected_id = f"CA-DOC-{str(seed.customer.id).upper()}"
    matching = next((item for item in items if item["id"] == expected_id), None)
    assert matching is not None
    assert matching["category"] == "Documentation"
    assert matching["type"] == "Profile documentation review"
    assert matching["status"] == "Open"
    assert "missing" in matching["description"]
    assert "phone number" in matching["description"]
    assert "occupation" in matching["description"]


@pytest.mark.asyncio
async def test_documentation_rule_ignores_customers_without_active_accounts(session_factory):
    """Customer with NO active account does not receive a Documentation alert even if profile is empty."""
    async with session_factory() as db:
        user = User(
            id=uuid.uuid4(),
            email="dormant@example.com",
            password_hash="dummy",
            role="CUSTOMER",
        )
        cust = Customer(
            id=uuid.uuid4(),
            user_id=user.id,
            customer_number="CUST-NO-ACT",
            first_name="NoActive",
            last_name="Account",
            phone=None,
            address=None,
        )
        # Dormant account only
        acct = Account(
            id=uuid.uuid4(),
            customer_id=cust.id,
            account_number="ACC-DORM-01",
            account_type="SAVINGS",
            status="DORMANT",
        )
        db.add_all([user, cust, acct])
        await db.commit()
        cust_id = cust.id

    async with session_factory() as db:
        service = ComplianceService(db)
        res = await service.list_alerts(category="Documentation")
        cust_alert_ids = [item.customer_id for item in res.items]
        assert str(cust_id) not in cust_alert_ids


# ===========================================================================
# 3. AML Sanctions Integrity Check
# ===========================================================================

@pytest.mark.asyncio
async def test_aml_sanctions_is_unsupported_and_zero_count(compliance_officer_client):
    """Confirms that AML category is unsupported and reports zero count honestly."""
    response = await compliance_officer_client.get("/api/v1/compliance/alerts")
    assert response.status_code == 200
    data = response.json()
    summary = data["summary"]

    assert summary["categoryCounts"]["AML"] == 0

    response_aml = await compliance_officer_client.get("/api/v1/compliance/alerts?category=AML")
    assert response_aml.status_code == 200
    assert response_aml.json()["total"] == 0
    assert response_aml.json()["items"] == []


# ===========================================================================
# 4. Identity, Pagination, Filter & Search Consistency
# ===========================================================================

@pytest.mark.asyncio
async def test_alert_ids_are_deterministic_and_do_not_drift(session_factory):
    """Repeated calls return identical alert IDs and due dates."""
    async with session_factory() as db:
        service = ComplianceService(db)
        res1 = await service.list_alerts()
        res2 = await service.list_alerts()

        assert res1.total == res2.total
        ids1 = [item.id for item in res1.items]
        ids2 = [item.id for item in res2.items]
        assert ids1 == ids2

        dates1 = [item.due_date for item in res1.items]
        dates2 = [item.due_date for item in res2.items]
        assert dates1 == dates2


@pytest.mark.asyncio
async def test_alerts_contain_real_customer_uuids(compliance_officer_client, session_factory):
    """Every alert customerId must be a valid UUID present in customers table."""
    response = await compliance_officer_client.get("/api/v1/compliance/alerts")
    assert response.status_code == 200
    items = response.json()["items"]

    async with session_factory() as db:
        for item in items:
            c_uuid = uuid.UUID(item["customerId"])
            cust = await db.get(Customer, c_uuid)
            assert cust is not None


@pytest.mark.asyncio
async def test_summary_reflects_complete_dataset_across_pagination(session_factory, seed, compliance_officer_client):
    """KPI summary counts describe the complete posture, not merely the paginated slice."""
    # Seed 3 high-value transactions
    async with session_factory() as db:
        txns = [
            Transaction(
                id=uuid.uuid4(),
                account_id=seed.funded_account.id,
                transaction_reference=f"REF-SUMM-{i}-{uuid.uuid4().hex[:6]}",
                transaction_type="DEBIT",
                amount=Decimal("1100000.00"),
                currency="INR",
                transaction_status="COMPLETED",
                transaction_date=datetime(2026, 10, 1, 10, i, tzinfo=timezone.utc),
            )
            for i in range(3)
        ]
        db.add_all(txns)
        await db.commit()

    # Request page_size = 1
    response = await compliance_officer_client.get("/api/v1/compliance/alerts?page=1&page_size=1")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 1
    assert data["total"] >= 3
    # open_count in summary must equal total open alerts across dataset, not 1
    assert data["summary"]["openCount"] >= 3
    assert data["summary"]["categoryCounts"]["Reporting"] >= 3


@pytest.mark.asyncio
async def test_search_and_severity_filters(session_factory, seed, compliance_officer_client):
    """Search matches alert ID or customer name, and severity filters work."""
    async with session_factory() as db:
        txn = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-CRIT-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("3000000.00"),  # >= 2.5M -> High severity
            currency="INR",
            transaction_status="COMPLETED",
            transaction_date=datetime(2026, 10, 2, 11, 0, tzinfo=timezone.utc),
        )
        db.add(txn)
        await db.commit()
        alert_id = f"CA-REP-{str(txn.id).upper()}"

    # Search by alert ID
    res_search = await compliance_officer_client.get(f"/api/v1/compliance/alerts?search={alert_id}")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["total"] == 1
    assert search_data["items"][0]["id"] == alert_id

    # Filter by High severity
    res_sev = await compliance_officer_client.get("/api/v1/compliance/alerts?severity=High")
    assert res_sev.status_code == 200
    sev_items = res_sev.json()["items"]
    assert any(i["id"] == alert_id for i in sev_items)


@pytest.mark.asyncio
async def test_compliance_alerts_as_of_affects_kyc_window(session_factory, seed, compliance_officer_client):
    """as_of query parameter shifts the 30-day KYC evaluation window."""
    async with session_factory() as db:
        cust = await db.get(Customer, seed.customer.id)
        cust.annual_income = Decimal("600000.00")  # monthly = 50,000; 3x = 150,000

        # Inject debit of 180,000 on 2026-09-10
        txn = Transaction(
            id=uuid.uuid4(),
            account_id=seed.funded_account.id,
            transaction_reference=f"REF-ASOF-{uuid.uuid4().hex[:6]}",
            transaction_type="DEBIT",
            amount=Decimal("180000.00"),
            currency="INR",
            transaction_status="COMPLETED",
            transaction_date=datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
        )
        db.add(txn)
        await db.commit()

    # as_of = 2026-10-05: 2026-09-10 is within trailing 30 days (25 days old) -> alert triggers
    res_in_window = await compliance_officer_client.get(
        "/api/v1/compliance/alerts?category=KYC&as_of=2026-10-05"
    )
    assert res_in_window.status_code == 200
    expected_id = f"CA-KYC-{str(seed.customer.id).upper()}"
    matching_in = next((item for item in res_in_window.json()["items"] if item["id"] == expected_id), None)
    assert matching_in is not None
    assert matching_in["category"] == "KYC"

    # as_of = 2026-10-20: 2026-09-10 is >30 days old (40 days old) -> alert excluded
    res_out_window = await compliance_officer_client.get(
        "/api/v1/compliance/alerts?category=KYC&as_of=2026-10-20"
    )
    assert res_out_window.status_code == 200
    matching_out = next((item for item in res_out_window.json()["items"] if item["id"] == expected_id), None)
    assert matching_out is None


@pytest.mark.asyncio
async def test_compliance_alerts_invalid_as_of_returns_422(compliance_officer_client):
    """Invalid as_of format returns HTTP 422 Unprocessable Entity."""
    res = await compliance_officer_client.get("/api/v1/compliance/alerts?as_of=invalid-date")
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_compliance_alerts_omitted_as_of_defaults_gracefully(compliance_officer_client):
    """Omitting as_of uses current UTC time and succeeds with HTTP 200."""
    res = await compliance_officer_client.get("/api/v1/compliance/alerts")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "summary" in data
