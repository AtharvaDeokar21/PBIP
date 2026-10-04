async def test_list_insurance_products(client):
    response = await client.get("/api/v1/insurance/products")

    assert response.status_code == 200
    assert {p["insurance_type"] for p in response.json()} >= {"LIFE", "HEALTH"}


async def test_get_insurance_product(client, seed):
    response = await client.get(f"/api/v1/insurance/products/{seed.insurance_product.id}")

    assert response.status_code == 200
    assert response.json()["name"] == seed.insurance_product.name
