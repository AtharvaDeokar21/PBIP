async def test_list_recommendations(client, seed):
    response = await client.get("/api/v1/recommendations")

    assert response.status_code == 200
    recommendations = response.json()
    assert len(recommendations) == 1
    assert recommendations[0]["product_id"] == str(seed.investment_product.id)
    assert recommendations[0]["status"] == "ACTIVE"
