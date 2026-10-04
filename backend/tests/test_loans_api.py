def _loan_request(seed) -> dict:
    product = seed.loan_product
    return {
        "loan_product_id": str(product.id),
        "requested_amount": float(product.min_amount),
        "tenure_months": product.max_tenure_months,
    }


async def test_list_loan_products(client):
    response = await client.get("/api/v1/loans/products")

    assert response.status_code == 200
    assert {p["loan_type"] for p in response.json()} >= {"PERSONAL", "HOME", "EDUCATION"}


async def test_get_loan_product(client, seed):
    response = await client.get(f"/api/v1/loans/products/{seed.loan_product.id}")

    assert response.status_code == 200
    assert response.json()["name"] == seed.loan_product.name


async def test_check_eligibility(client, seed):
    response = await client.post("/api/v1/loans/eligibility", json=_loan_request(seed))

    assert response.status_code == 200
    body = response.json()
    assert body["loan_product_id"] == str(seed.loan_product.id)
    assert float(body["estimated_emi"]) > 0
    assert body["reasons"]


async def test_apply_and_track_loan(client, seed):
    created = await client.post("/api/v1/loans/applications", json=_loan_request(seed))

    assert created.status_code == 201, created.text
    application = created.json()
    assert application["status"] == "SUBMITTED"
    assert float(application["emi_amount"]) > 0

    listing = await client.get("/api/v1/loans/applications")
    detail = await client.get(f"/api/v1/loans/applications/{application['id']}")

    assert listing.status_code == 200
    assert [a["id"] for a in listing.json()] == [application["id"]]
    assert detail.status_code == 200
    assert detail.json()["id"] == application["id"]
