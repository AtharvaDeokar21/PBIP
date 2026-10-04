PAYEE = {
    "name": "Rahul Sharma",
    "account_number": "123456789012",
    "bank_name": "HDFC Bank",
    "ifsc_code": "HDFC0001234",
    "nickname": "Rahul",
}


async def _create_payee(client) -> dict:
    response = await client.post("/api/v1/payees", json=PAYEE)
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_payee(client):
    payee = await _create_payee(client)

    assert payee["name"] == PAYEE["name"]
    assert payee["account_number"] == "XXXX9012"
    assert payee["is_verified"] is False
    assert payee["is_active"] is True


async def test_list_payees(client):
    payee = await _create_payee(client)

    response = await client.get("/api/v1/payees")

    assert response.status_code == 200
    assert [p["id"] for p in response.json()] == [payee["id"]]


async def test_update_payee(client):
    payee = await _create_payee(client)

    response = await client.patch(f"/api/v1/payees/{payee['id']}", json={"nickname": "Bro"})

    assert response.status_code == 200
    assert response.json()["nickname"] == "Bro"


async def test_delete_payee(client):
    payee = await _create_payee(client)

    response = await client.delete(f"/api/v1/payees/{payee['id']}")

    assert response.status_code == 204
    remaining = await client.get("/api/v1/payees")
    assert remaining.json() == []
