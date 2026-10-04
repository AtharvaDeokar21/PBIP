async def test_list_billers(client, seed):
    response = await client.get("/api/v1/billers")

    assert response.status_code == 200
    assert [b["id"] for b in response.json()] == [str(seed.biller.id)]


async def test_pay_bill(client, seed):
    response = await client.post(
        "/api/v1/bills/pay",
        json={
            "account_id": str(seed.funded_account.id),
            "biller_id": str(seed.biller.id),
            "amount": 500,
            "due_date": "2026-10-05",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["reference_number"].startswith("BILL-")


async def test_bill_history(client, seed):
    await client.post(
        "/api/v1/bills/pay",
        json={
            "account_id": str(seed.funded_account.id),
            "biller_id": str(seed.biller.id),
            "amount": 300,
        },
    )

    response = await client.get("/api/v1/bills/history")

    assert response.status_code == 200
    assert response.json()["total"] == 1
