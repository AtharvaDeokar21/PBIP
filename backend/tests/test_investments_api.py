async def test_list_investment_products(client):
    response = await client.get("/api/v1/investments/products", params={"product_type": "MUTUAL_FUND"})

    assert response.status_code == 200
    products = response.json()
    assert products
    assert all(p["product_type"] == "MUTUAL_FUND" for p in products)


async def test_get_investment_product(client, seed):
    response = await client.get(f"/api/v1/investments/products/{seed.investment_product.id}")

    assert response.status_code == 200
    assert response.json()["name"] == seed.investment_product.name


async def test_create_investment_without_debit(client, seed):
    amount = float(seed.investment_product.minimum_investment)

    response = await client.post(
        "/api/v1/investments",
        json={"investment_product_id": str(seed.investment_product.id), "amount_invested": amount},
    )

    assert response.status_code == 201, response.text
    assert response.json()["status"] == "ACTIVE"
    assert float(response.json()["amount_invested"]) == amount


async def test_create_investment_with_account_debit(client, seed):
    response = await client.post(
        "/api/v1/investments",
        json={
            "investment_product_id": str(seed.investment_product.id),
            "amount_invested": float(seed.investment_product.minimum_investment),
            "source_account_id": str(seed.funded_account.id),
        },
    )

    assert response.status_code == 201, response.text


async def test_list_my_investments(client, seed):
    await client.post(
        "/api/v1/investments",
        json={
            "investment_product_id": str(seed.investment_product.id),
            "amount_invested": float(seed.investment_product.minimum_investment),
        },
    )

    response = await client.get("/api/v1/investments")

    assert response.status_code == 200
    assert len(response.json()) == 1
