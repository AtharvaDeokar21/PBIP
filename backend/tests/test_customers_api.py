async def test_get_my_profile(client, seed):
    response = await client.get("/api/v1/customers/me")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(seed.customer.id)
    assert body["customer_number"] == seed.customer.customer_number
    assert body["email"] == seed.user.email


async def test_update_my_profile(client):
    response = await client.patch(
        "/api/v1/customers/me",
        json={"city": "Pune", "occupation": "Architect"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Pune"
    assert body["occupation"] == "Architect"


async def test_get_my_financial_summary(client, seed):
    response = await client.get("/api/v1/customers/me/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_accounts"] == len(seed.accounts)
    assert body["balances_by_type"]
