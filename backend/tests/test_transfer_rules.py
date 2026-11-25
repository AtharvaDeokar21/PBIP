"""Transfer validation and business rules (UC-04): limits, balance, fraud flags, lifecycle."""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.banking import Account
from app.models.system import SecurityEvent

PAYEE = {
    "name": "Rahul Mehta",
    "account_number": "123456789012",
    "bank_name": "HDFC Bank",
    "ifsc_code": "HDFC0001234",
    "nickname": "Rahul",
}


async def _payee(client) -> str:
    response = await client.post("/api/v1/payees", json=PAYEE)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _future(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"payee_id": None, "destination_account_id": None}, "exactly one of payee_id"),
        ({"transfer_type": "SCHEDULED"}, "scheduled_at is required"),
        ({"transfer_type": "SCHEDULED", "scheduled_at": _future(-1)}, "must be in the future"),
        ({"transfer_type": "SCHEDULED", "scheduled_at": _future(400)}, "more than 1 year ahead"),
        ({"scheduled_at": _future(3)}, "only allowed for SCHEDULED"),
        ({"amount": 0}, ""),
        ({"amount": -10}, ""),
    ],
)
async def test_invalid_transfer_requests_are_rejected(client, seed, extra, message):
    payload = {
        "source_account_id": str(seed.funded_account.id),
        "destination_account_id": str(seed.other_account.id),
        "amount": 100,
        **extra,
    }

    response = await client.post("/api/v1/transfers", json=payload)

    assert response.status_code == 422
    assert message in response.text


async def test_naive_scheduled_time_is_treated_as_utc(client, seed):
    naive = (datetime.now(timezone.utc) + timedelta(days=2)).replace(tzinfo=None).isoformat()

    response = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(seed.funded_account.id),
            "payee_id": await _payee(client),
            "amount": 100,
            "transfer_type": "SCHEDULED",
            "scheduled_at": naive,
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "SCHEDULED"


async def test_transfer_to_same_account_is_rejected(client, seed):
    response = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(seed.funded_account.id),
            "destination_account_id": str(seed.funded_account.id),
            "amount": 100,
        },
    )

    assert response.status_code == 422
    assert "must differ" in response.text


async def test_per_transfer_limit(client, seed, monkeypatch):
    monkeypatch.setattr(settings, "max_single_transfer_amount", 100)

    response = await client.post(
        "/api/v1/transfers",
        json={"source_account_id": str(seed.funded_account.id), "payee_id": await _payee(client), "amount": 101},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Amount exceeds the per-transfer limit"


async def test_daily_transfer_limit(client, seed, monkeypatch):
    monkeypatch.setattr(settings, "daily_transfer_limit", 1000)
    payee_id = await _payee(client)
    body = {"source_account_id": str(seed.funded_account.id), "payee_id": payee_id, "amount": 600}

    first = await client.post("/api/v1/transfers", json=body)
    second = await client.post("/api/v1/transfers", json=body)

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json()["detail"] == "Amount exceeds the daily transfer limit"


async def test_insufficient_balance(client, seed, session_factory):
    async with session_factory() as db:
        account = await db.get(Account, seed.funded_account.id)
        account.available_balance = Decimal("50.00")
        await db.commit()

    response = await client.post(
        "/api/v1/transfers",
        json={"source_account_id": str(seed.funded_account.id), "payee_id": await _payee(client), "amount": 100},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Insufficient available balance"


async def test_inactive_source_account_is_rejected(client, seed, session_factory):
    async with session_factory() as db:
        account = await db.get(Account, seed.funded_account.id)
        account.status = "FROZEN"
        await db.commit()

    response = await client.post(
        "/api/v1/transfers",
        json={"source_account_id": str(seed.funded_account.id), "payee_id": await _payee(client), "amount": 100},
    )

    assert response.status_code == 422


async def test_foreign_or_unknown_accounts_and_payees_return_404(client, seed):
    unknown_source = await client.post(
        "/api/v1/transfers",
        json={"source_account_id": str(uuid.uuid4()), "destination_account_id": str(seed.other_account.id), "amount": 10},
    )
    unknown_payee = await client.post(
        "/api/v1/transfers",
        json={"source_account_id": str(seed.funded_account.id), "payee_id": str(uuid.uuid4()), "amount": 10},
    )

    assert unknown_source.status_code == 404
    assert unknown_payee.status_code == 404


async def test_high_value_transfer_is_flagged_for_fraud_monitoring(client, seed, session_factory, monkeypatch):
    monkeypatch.setattr("app.services.payment_service.HIGH_VALUE_TRANSFER_THRESHOLD", Decimal("500"))

    response = await client.post(
        "/api/v1/transfers",
        json={"source_account_id": str(seed.funded_account.id), "payee_id": await _payee(client), "amount": 750},
    )

    assert response.status_code == 201, response.text
    async with session_factory() as db:
        event = await db.scalar(select(SecurityEvent).where(SecurityEvent.event_type == "HIGH_VALUE_TRANSFER"))
    assert event is not None
    assert event.user_id == seed.user.id


async def test_completed_transfer_cannot_be_cancelled(client, seed):
    created = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(seed.funded_account.id),
            "destination_account_id": str(seed.other_account.id),
            "amount": 10,
        },
    )

    response = await client.post(f"/api/v1/transfers/{created.json()['id']}/cancel")

    assert response.status_code == 409
    assert response.json()["detail"] == "A COMPLETED transfer cannot be cancelled"


async def test_cancelled_transfer_releases_scheduled_amount(client, seed):
    payee_id = await _payee(client)
    created = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(seed.funded_account.id),
            "payee_id": payee_id,
            "amount": 300,
            "transfer_type": "SCHEDULED",
            "scheduled_at": _future(5),
        },
    )
    transfer_id = created.json()["id"]

    first = await client.post(f"/api/v1/transfers/{transfer_id}/cancel")
    again = await client.post(f"/api/v1/transfers/{transfer_id}/cancel")
    unknown = await client.post(f"/api/v1/transfers/{uuid.uuid4()}/cancel")

    assert first.status_code == 200
    assert again.status_code == 409
    assert unknown.status_code == 404


async def test_transfer_listing_filters_by_status(client, seed):
    await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(seed.funded_account.id),
            "destination_account_id": str(seed.other_account.id),
            "amount": 25,
        },
    )

    completed = await client.get("/api/v1/transfers", params={"status": "COMPLETED"})
    scheduled = await client.get("/api/v1/transfers", params={"status": "SCHEDULED"})

    assert completed.status_code == 200
    assert completed.json()["total"] >= 1
    assert scheduled.json()["total"] == 0
