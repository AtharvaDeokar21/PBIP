async def test_list_account_transactions(client, seed):
    account = seed.funded_account

    response = await client.get(
        f"/api/v1/accounts/{account.id}/transactions",
        params={"page": 1, "page_size": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["total"] > 0
    assert 0 < len(body["items"]) <= 5
    assert all(t["account_id"] == str(account.id) for t in body["items"])


async def test_list_account_transactions_with_filters(client, seed):
    account = seed.funded_account

    response = await client.get(
        f"/api/v1/accounts/{account.id}/transactions",
        params={"transaction_status": "COMPLETED", "min_amount": 0},
    )

    assert response.status_code == 200
    assert all(t["transaction_status"] == "COMPLETED" for t in response.json()["items"])


async def test_get_transaction(client, seed):
    account = seed.funded_account
    listing = await client.get(f"/api/v1/accounts/{account.id}/transactions")
    transaction_id = listing.json()["items"][0]["id"]

    response = await client.get(f"/api/v1/transactions/{transaction_id}")

    assert response.status_code == 200
    assert response.json()["id"] == transaction_id
