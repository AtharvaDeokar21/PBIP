async def test_list_accounts(client, seed):
    response = await client.get("/api/v1/accounts")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(seed.accounts)
    assert {a["id"] for a in body["items"]} == {str(a.id) for a in seed.accounts}
    assert all(a["account_number"].startswith("XXXX") for a in body["items"])


async def test_get_account(client, seed):
    account = seed.funded_account

    response = await client.get(f"/api/v1/accounts/{account.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(account.id)
    assert body["account_type"] == account.account_type
    assert body["account_number"] == f"XXXX{account.account_number[-4:]}"
