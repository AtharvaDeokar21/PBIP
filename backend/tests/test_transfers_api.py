from datetime import datetime, timedelta, timezone
from decimal import Decimal

PAYEE = {
    "name": "Sneha Patil",
    "account_number": "987654321098",
    "bank_name": "ICICI Bank",
    "ifsc_code": "ICIC0004321",
    "nickname": "Sneha",
}


async def _create_payee(client) -> str:
    response = await client.post("/api/v1/payees", json=PAYEE)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _available_balance(client, account_id) -> Decimal:
    response = await client.get(f"/api/v1/accounts/{account_id}")
    return Decimal(str(response.json()["available_balance"]))


async def test_immediate_transfer_to_payee(client, seed):
    source = seed.funded_account
    payee_id = await _create_payee(client)
    balance_before = await _available_balance(client, source.id)

    response = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(source.id),
            "payee_id": payee_id,
            "amount": 500,
            "transfer_type": "IMMEDIATE",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["reference_number"].startswith("TRF-")
    assert await _available_balance(client, source.id) == balance_before - 500


async def test_internal_transfer_between_own_accounts(client, seed):
    source, destination = seed.funded_account, seed.other_account
    destination_before = await _available_balance(client, destination.id)

    response = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(source.id),
            "destination_account_id": str(destination.id),
            "amount": 250,
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "COMPLETED"
    assert await _available_balance(client, destination.id) == destination_before + 250


async def test_scheduled_transfer_and_cancel(client, seed):
    payee_id = await _create_payee(client)
    scheduled_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    created = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(seed.funded_account.id),
            "payee_id": payee_id,
            "amount": 1000,
            "transfer_type": "SCHEDULED",
            "scheduled_at": scheduled_at,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "SCHEDULED"

    response = await client.post(f"/api/v1/transfers/{created.json()['id']}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


async def test_list_and_get_transfers(client, seed):
    created = await client.post(
        "/api/v1/transfers",
        json={
            "source_account_id": str(seed.funded_account.id),
            "destination_account_id": str(seed.other_account.id),
            "amount": 100,
        },
    )
    transfer_id = created.json()["id"]

    listing = await client.get("/api/v1/transfers")
    detail = await client.get(f"/api/v1/transfers/{transfer_id}")

    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["id"] == transfer_id
    assert detail.status_code == 200
    assert detail.json()["id"] == transfer_id
