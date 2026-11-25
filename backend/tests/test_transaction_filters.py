"""Transaction search and filtering (UC-02 / statement views) and input validation."""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models.banking import Transaction


async def _transactions(session_factory, account_id) -> list[Transaction]:
    async with session_factory() as db:
        return list(await db.scalars(select(Transaction).where(Transaction.account_id == account_id)))


def _url(account) -> str:
    return f"/api/v1/accounts/{account.id}/transactions"


async def test_filter_by_transaction_type(client, seed, session_factory):
    account = seed.funded_account
    expected = sum(1 for t in await _transactions(session_factory, account.id) if t.transaction_type == "DEBIT")

    response = await client.get(_url(account), params={"transaction_type": "debit", "page_size": 100})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == expected
    assert all(item["transaction_type"] == "DEBIT" for item in body["items"])


async def test_filter_by_amount_range(client, seed):
    response = await client.get(
        _url(seed.funded_account), params={"min_amount": 100, "max_amount": 5000, "page_size": 100}
    )

    assert response.status_code == 200
    for item in response.json()["items"]:
        assert Decimal("100") <= Decimal(str(item["amount"])) <= Decimal("5000")


async def test_filter_by_date_range(client, seed, session_factory):
    txns = await _transactions(session_factory, seed.funded_account.id)
    day = max(t.transaction_date for t in txns).date()

    response = await client.get(
        _url(seed.funded_account), params={"start_date": day.isoformat(), "end_date": day.isoformat()}
    )

    assert response.status_code == 200
    assert response.json()["total"] >= 1
    for item in response.json()["items"]:
        assert item["transaction_date"].startswith(day.isoformat())


async def test_filter_by_category_and_status(client, seed, session_factory):
    txn = (await _transactions(session_factory, seed.funded_account.id))[0]

    response = await client.get(
        _url(seed.funded_account),
        params={"category": txn.category.lower(), "transaction_status": txn.transaction_status.lower(), "page_size": 100},
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert str(txn.id) in ids


async def test_search_matches_description_or_merchant(client, seed, session_factory):
    txn = next(t for t in await _transactions(session_factory, seed.funded_account.id) if t.merchant_name)
    term = txn.merchant_name[:4]

    response = await client.get(_url(seed.funded_account), params={"search": term, "page_size": 100})

    assert response.status_code == 200
    assert str(txn.id) in [item["id"] for item in response.json()["items"]]


async def test_search_wildcards_are_matched_literally(client, seed):
    response = await client.get(_url(seed.funded_account), params={"search": "%_%"})

    assert response.status_code == 200
    assert response.json()["total"] == 0


async def test_pagination_metadata(client, seed):
    response = await client.get(_url(seed.funded_account), params={"page": 1, "page_size": 2})

    body = response.json()
    assert response.status_code == 200
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) <= 2


@pytest.mark.parametrize(
    "params",
    [
        {"start_date": date.today().isoformat(), "end_date": (date.today() - timedelta(days=1)).isoformat()},
        {"min_amount": 500, "max_amount": 100},
        {"min_amount": -1},
        {"page_size": 1000},
        {"page": 0},
    ],
)
async def test_invalid_filters_are_rejected(client, seed, params):
    response = await client.get(_url(seed.funded_account), params=params)

    assert response.status_code == 422


async def test_transactions_of_foreign_account_return_404(client):
    response = await client.get(f"/api/v1/accounts/{uuid.uuid4()}/transactions")

    assert response.status_code == 404


async def test_get_single_transaction_and_unknown_id(client, seed, session_factory):
    txn = (await _transactions(session_factory, seed.funded_account.id))[0]

    found = await client.get(f"/api/v1/transactions/{txn.id}")
    missing = await client.get(f"/api/v1/transactions/{uuid.uuid4()}")

    assert found.status_code == 200
    assert found.json()["id"] == str(txn.id)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Transaction not found"
