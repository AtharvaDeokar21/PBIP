from app.core.config import settings


async def test_chat_recommendations_tool_lists_active_recommendations(client, seed, monkeypatch):
    # Keyword tools only; never call the LLM provider from tests.
    monkeypatch.setattr(settings, "groq_api_key", None)

    response = await client.post("/api/v1/ai/chat", json={"message": "Any recommendations for me?"})

    assert response.status_code == 200
    body = response.json()
    assert body["tool_used"] == "get_recommendations"
    assert "Investment: Regular surplus balance" in body["response"]
