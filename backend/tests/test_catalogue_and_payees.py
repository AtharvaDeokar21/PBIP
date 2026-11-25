"""Product catalogue filters, payee rules, loan eligibility edge cases and behaviour-analytics filters."""

import uuid
from decimal import Decimal

from app.models.identity import User

PAYEE = {
    "name": "Kavya Iyer",
    "account_number": "555566667777",
    "bank_name": "Axis Bank",
    "ifsc_code": "UTIB0000123",
    "nickname": "Kavya",
}


async def test_insurance_filters_and_unknown_product(client, seed):
    product = seed.insurance_product

    matching = await client.get(
        "/api/v1/insurance/products",
        params={"insurance_type": product.insurance_type.lower(), "risk_level": product.risk_level.lower()},
    )
    none = await client.get("/api/v1/insurance/products", params={"insurance_type": "SPACE_TRAVEL"})
    missing = await client.get(f"/api/v1/insurance/products/{uuid.uuid4()}")

    assert str(product.id) in [p["id"] for p in matching.json()]
    assert none.json() == []
    assert missing.status_code == 404


async def test_investment_filters_and_unknown_product(client, seed):
    product = seed.investment_product

    matching = await client.get(
        "/api/v1/investments/products",
        params={"product_type": product.product_type.lower(), "risk_level": product.risk_level.lower()},
    )
    missing = await client.get(f"/api/v1/investments/products/{uuid.uuid4()}")

    assert str(product.id) in [p["id"] for p in matching.json()]
    assert all(p["product_type"] == product.product_type for p in matching.json())
    assert missing.status_code == 404


async def test_investment_below_minimum_is_rejected(client, seed):
    response = await client.post(
        "/api/v1/investments",
        json={
            "investment_product_id": str(seed.investment_product.id),
            "amount_invested": float(Decimal(seed.investment_product.minimum_investment) - 1),
            "source_account_id": str(seed.funded_account.id),
        },
    )

    assert response.status_code == 422


async def test_investment_debits_source_account(client, seed):
    before = (await client.get(f"/api/v1/accounts/{seed.funded_account.id}")).json()["available_balance"]
    amount = float(seed.investment_product.minimum_investment)

    response = await client.post(
        "/api/v1/investments",
        json={
            "investment_product_id": str(seed.investment_product.id),
            "amount_invested": amount,
            "source_account_id": str(seed.funded_account.id),
        },
    )
    after = (await client.get(f"/api/v1/accounts/{seed.funded_account.id}")).json()["available_balance"]

    assert response.status_code == 201, response.text
    assert Decimal(str(before)) - Decimal(str(after)) == Decimal(str(amount))
    assert len((await client.get("/api/v1/investments")).json()) == 1


async def test_loan_product_filter_and_unknown_product(client, seed):
    personal = await client.get("/api/v1/loans/products", params={"loan_type": "personal"})
    missing = await client.get(f"/api/v1/loans/products/{uuid.uuid4()}")

    assert personal.status_code == 200
    assert personal.json()
    assert all(p["loan_type"] == "PERSONAL" for p in personal.json())
    assert missing.status_code == 404


async def test_unknown_loan_application_returns_404(client):
    response = await client.get(f"/api/v1/loans/applications/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_duplicate_payee_is_conflict(client):
    first = await client.post("/api/v1/payees", json=PAYEE)
    duplicate = await client.post("/api/v1/payees", json=PAYEE)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "A payee with these bank details already exists"


async def test_payee_input_validation(client):
    bad_ifsc = await client.post("/api/v1/payees", json={**PAYEE, "ifsc_code": "BAD"})
    bad_account = await client.post("/api/v1/payees", json={**PAYEE, "account_number": "12ab"})

    assert bad_ifsc.status_code == 422
    assert bad_account.status_code == 422


async def test_unknown_payee_update_and_delete_return_404(client):
    update = await client.patch(f"/api/v1/payees/{uuid.uuid4()}", json={"nickname": "x"})
    delete = await client.delete(f"/api/v1/payees/{uuid.uuid4()}")

    assert update.status_code == 404
    assert delete.status_code == 404


async def test_deleted_payee_is_hidden_and_cannot_receive_transfers(client, seed):
    payee_id = (await client.post("/api/v1/payees", json=PAYEE)).json()["id"]

    deleted = await client.delete(f"/api/v1/payees/{payee_id}")
    listing = await client.get("/api/v1/payees")
    transfer = await client.post(
        "/api/v1/transfers",
        json={"source_account_id": str(seed.funded_account.id), "payee_id": payee_id, "amount": 10},
    )

    assert deleted.status_code in (200, 204)
    assert payee_id not in [p["id"] for p in listing.json()]
    assert transfer.status_code in (404, 422)


async def test_behaviour_filters_for_relationship_manager(client, seed, session_factory):
    async with session_factory() as db:
        user = await db.get(User, seed.user.id)
        user.role = "RELATIONSHIP_MANAGER"
        await db.commit()

    everyone = await client.get("/api/v1/analytics/behaviour/filters")
    searched = await client.get(
        "/api/v1/analytics/behaviour/filters", params={"search": seed.customer.last_name[:3]}
    )

    assert everyone.status_code == 200
    body = everyone.json()
    assert set(body["products"]) == {"Savings", "Loans", "Investments", "Insurance"}
    assert body["segments"]
    assert searched.status_code == 200


async def test_customer_cannot_read_behaviour_filters(client):
    response = await client.get("/api/v1/analytics/behaviour/filters")

    assert response.status_code == 403
