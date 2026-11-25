"""Service applications built by the shared app factory: request IDs, metrics, logging, roots."""

import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.admin_main import app as admin_app
from app.core.database import get_db
from app.customer_main import app as customer_app
from tests.conftest import GENERATED_PASSWORD


@pytest.fixture
async def service_client(session_factory, seed):
    async def _get_test_db():
        async with session_factory() as session:
            yield session

    customer_app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(transport=ASGITransport(app=customer_app), base_url="http://test") as ac:
        yield ac
    customer_app.dependency_overrides.clear()


async def test_request_id_is_generated_and_returned(service_client):
    response = await service_client.get("/api/v1/health")

    assert response.status_code == 200
    assert len(response.headers["x-request-id"]) == 32


async def test_caller_request_id_is_propagated(service_client):
    response = await service_client.get("/api/v1/health", headers={"X-Request-ID": "trace-abc-123"})

    assert response.headers["x-request-id"] == "trace-abc-123"


async def test_access_log_records_route_status_and_request_id(service_client, seed, caplog):
    caplog.set_level(logging.DEBUG, logger="credora.access")

    await service_client.post(
        "/api/v1/auth/login",
        json={"email": seed.user.email, "password": GENERATED_PASSWORD},
        headers={"X-Request-ID": "login-trace"},
    )

    record = next(r for r in caplog.records if r.getMessage() == "request completed" and r.path == "/api/v1/auth/login")
    assert record.status == 200
    assert record.route == "/api/v1/auth/login"
    assert record.levelno == logging.INFO
    assert record.duration_ms >= 0


async def test_health_checks_are_logged_quietly(service_client, caplog):
    caplog.set_level(logging.DEBUG, logger="credora.access")

    await service_client.get("/api/v1/health")

    record = next(r for r in caplog.records if getattr(r, "path", None) == "/api/v1/health")
    assert record.levelno == logging.DEBUG


async def test_unknown_route_has_no_route_template(service_client, caplog):
    caplog.set_level(logging.DEBUG, logger="credora.access")

    response = await service_client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    record = next(r for r in caplog.records if getattr(r, "path", None) == "/api/v1/does-not-exist")
    assert record.route is None


async def test_metrics_endpoint_exposes_request_metrics(service_client):
    await service_client.get("/api/v1/health")

    response = await service_client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert "http_requests_inprogress" in response.text


async def test_service_roots_identify_the_service():
    async with AsyncClient(transport=ASGITransport(app=customer_app), base_url="http://test") as c:
        customer_root = (await c.get("/")).json()
    async with AsyncClient(transport=ASGITransport(app=admin_app), base_url="http://test") as c:
        admin_root = (await c.get("/")).json()

    assert customer_root["service"] == "Customer Service"
    assert admin_root["service"] == "Admin Service"
    assert customer_root["docs"] == "/docs"


async def test_customer_service_does_not_serve_admin_routes(service_client):
    response = await service_client.get("/api/v1/fraud/alerts")

    assert response.status_code == 404
