"""Authentication and authorisation: registration, login outcomes, token checks, health."""

import uuid

from sqlalchemy import select

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.identity import Customer, User
from app.models.system import AuditLog, SecurityEvent
from tests.conftest import GENERATED_PASSWORD

NEW_CUSTOMER = {
    "email": "  Asha.Rao@Example.com ",
    "password": "Str0ng@Pass",
    "first_name": " Asha ",
    "last_name": "Rao",
    "phone": "+919800000000",
}


async def _events(session_factory, event_type: str) -> list[SecurityEvent]:
    async with session_factory() as db:
        return list(await db.scalars(select(SecurityEvent).where(SecurityEvent.event_type == event_type)))


async def test_register_creates_user_customer_and_audit_entry(client, session_factory):
    response = await client.post("/api/v1/auth/register", json={**NEW_CUSTOMER, "email": "asha.rao@example.com"})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "asha.rao@example.com"
    assert body["role"] == "CUSTOMER"
    async with session_factory() as db:
        user = await db.get(User, uuid.UUID(body["user_id"]))
        customer = await db.get(Customer, uuid.UUID(body["customer_id"]))
        audit = await db.scalar(select(AuditLog).where(AuditLog.action == "CUSTOMER_REGISTERED"))
    assert user.password_hash != NEW_CUSTOMER["password"]
    assert customer.first_name == "Asha"
    assert customer.customer_number.startswith("PBIP-")
    assert audit is not None and audit.user_id == user.id


async def test_registered_customer_can_log_in_with_normalised_email(client):
    await client.post("/api/v1/auth/register", json={**NEW_CUSTOMER, "email": "asha.rao@example.com"})

    response = await client.post(
        "/api/v1/auth/login", json={"email": "ASHA.RAO@example.com", "password": NEW_CUSTOMER["password"]}
    )

    assert response.status_code == 200
    assert response.json()["role"] == "CUSTOMER"
    assert response.json()["access_token"]


async def test_register_duplicate_email_is_conflict(client, seed):
    response = await client.post(
        "/api/v1/auth/register", json={**NEW_CUSTOMER, "email": seed.user.email.upper()}
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


async def test_register_rejects_weak_password_and_invalid_email(client):
    weak = await client.post("/api/v1/auth/register", json={**NEW_CUSTOMER, "email": "x@example.com", "password": "short"})
    bad_email = await client.post("/api/v1/auth/register", json={**NEW_CUSTOMER, "email": "not-an-email"})

    assert weak.status_code == 422
    assert bad_email.status_code == 422


async def test_login_unknown_email_records_security_event(client, session_factory):
    response = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": GENERATED_PASSWORD}
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    events = await _events(session_factory, "LOGIN_FAILED")
    assert any((e.event_metadata or {}).get("reason") == "unknown_email" for e in events)


async def test_login_wrong_password_records_security_event(client, seed, session_factory):
    response = await client.post(
        "/api/v1/auth/login", json={"email": seed.user.email, "password": "WrongPass@123"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
    events = await _events(session_factory, "LOGIN_FAILED")
    assert any(e.user_id == seed.user.id and e.event_metadata["reason"] == "invalid_password" for e in events)


async def test_successful_login_records_security_event_and_audit(client, seed, session_factory):
    # The client fixture logged in once already.
    events = await _events(session_factory, "LOGIN_SUCCESS")
    async with session_factory() as db:
        audit = await db.scalar(select(AuditLog).where(AuditLog.action == "USER_LOGIN", AuditLog.user_id == seed.user.id))
        user = await db.get(User, seed.user.id)

    assert any(e.user_id == seed.user.id for e in events)
    assert audit is not None
    assert user.last_login_at is not None


async def test_inactive_account_cannot_log_in_or_use_existing_token(client, seed, session_factory):
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        user.is_active = False
        await db.commit()

    login = await client.post("/api/v1/auth/login", json={"email": seed.user.email, "password": GENERATED_PASSWORD})
    me = await client.get("/api/v1/me")

    assert login.status_code == 401
    assert login.json()["detail"] == "Account is inactive"
    assert me.status_code == 401
    events = await _events(session_factory, "LOGIN_FAILED")
    assert any(e.event_metadata["reason"] == "inactive_account" for e in events)


async def test_me_returns_current_user(client, seed):
    response = await client.get("/api/v1/me")

    assert response.status_code == 200
    assert response.json()["email"] == seed.user.email
    assert response.json()["role"] == "CUSTOMER"


async def test_protected_endpoint_requires_token(client):
    response = await client.get("/api/v1/accounts", headers={"Authorization": ""})

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


async def test_tampered_token_is_rejected(client):
    token = client.headers["Authorization"] + "tampered"

    response = await client.get("/api/v1/accounts", headers={"Authorization": token})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


async def test_token_for_deleted_user_is_rejected(client):
    token = create_access_token(uuid.uuid4(), "CUSTOMER")

    response = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "User account is unavailable"


async def test_staff_role_cannot_use_customer_endpoints(client, seed, session_factory):
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        user.role = "FRAUD_ANALYST"
        await db.commit()

    response = await client.get("/api/v1/accounts")

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


async def test_staff_user_without_customer_profile_gets_404(client, seed, session_factory):
    async with session_factory() as db:
        customer = await db.get(Customer, seed.customer.id)
        await db.delete(customer)
        await db.commit()

    response = await client.get("/api/v1/customers/me")

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer profile not found"


async def test_health_reports_connected_database(client):
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "PBIP API", "database": "connected"}


async def test_health_reports_degraded_when_database_fails(client):
    class BrokenSession:
        async def execute(self, *args, **kwargs):
            raise ConnectionError("database unreachable")

    async def _broken_db():
        yield BrokenSession()

    previous = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = _broken_db
    try:
        response = await client.get("/api/v1/health")
    finally:
        app.dependency_overrides[get_db] = previous

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "disconnected"
