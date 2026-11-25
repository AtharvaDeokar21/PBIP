"""AI banking assistant: intent routing to banking tools, LLM fallback and conversation history."""

import uuid

import httpx
import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def _no_llm(monkeypatch):
    # Tests never call the real LLM provider.
    monkeypatch.setattr(settings, "groq_api_key", None)


@pytest.mark.parametrize(
    ("message", "tool", "expected_text"),
    [
        ("How much did I spend this month?", "get_spending_summary", "spending summary"),
        ("Show my account balance", "get_account_balance", "total available balance"),
        ("What loans am I eligible for?", "get_loan_products", "available loan products"),
        ("Show my recent transactions", "get_recent_transactions", "most recent transactions"),
        ("Do you have any advice for me?", "get_recommendations", "personalized recommendations"),
        ("How is my investment portfolio?", "get_customer_investments", "investment holdings"),
        ("Show my profile", "get_customer_profile", "Customer No"),
    ],
)
async def test_intent_routes_to_banking_tool(client, message, tool, expected_text):
    response = await client.post("/api/v1/ai/chat", json={"message": message})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tool_used"] == tool
    assert expected_text in body["response"]


async def test_balance_answer_masks_account_numbers(client, seed):
    response = await client.post("/api/v1/ai/chat", json={"message": "what is my balance"})

    text = response.json()["response"]
    for account in seed.accounts:
        assert account.account_number not in text
        assert f"...{account.account_number[-4:]}" in text


async def test_investment_answer_reflects_new_holding(client, seed):
    invest = await client.post(
        "/api/v1/investments",
        json={
            "investment_product_id": str(seed.investment_product.id),
            "source_account_id": str(seed.funded_account.id),
            "amount_invested": float(seed.investment_product.minimum_investment),
        },
    )
    assert invest.status_code == 201, invest.text

    response = await client.post("/api/v1/ai/chat", json={"message": "show my investments"})

    assert response.json()["tool_used"] == "get_customer_investments"
    assert "1 active investment(s)" in response.json()["response"]


async def test_unmatched_question_returns_help_without_llm(client, seed):
    response = await client.post("/api/v1/ai/chat", json={"message": "Tell me a joke"})

    body = response.json()
    assert body["tool_used"] is None
    assert f"Hello {seed.customer.first_name}" in body["response"]
    assert "I can help you with" in body["response"]


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _fake_client(payload=None, error: Exception | None = None):
    calls = []

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, **kwargs):
            calls.append((url, kwargs))
            if error:
                raise error
            return _FakeResponse(payload)

    return FakeAsyncClient, calls


async def test_general_question_is_answered_by_llm(client, monkeypatch):
    fake, calls = _fake_client({"choices": [{"message": {"content": "  A savings account earns interest.  "}}]})
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.api.ai.httpx.AsyncClient", fake)

    response = await client.post("/api/v1/ai/chat", json={"message": "What is a savings account?"})

    assert response.json()["response"] == "A savings account earns interest."
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url.endswith("/chat/completions")
    assert kwargs["json"]["messages"][-1]["content"] == "What is a savings account?"
    # Banking data is never sent to the LLM for general questions.
    assert len(kwargs["json"]["messages"]) == 2


async def test_llm_failure_falls_back_to_help_text(client, monkeypatch):
    fake, _ = _fake_client(error=httpx.ConnectError("provider down"))
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.api.ai.httpx.AsyncClient", fake)

    response = await client.post("/api/v1/ai/chat", json={"message": "What is inflation?"})

    assert response.status_code == 200
    assert "I can help you with" in response.json()["response"]


async def test_malformed_llm_payload_falls_back_to_help_text(client, monkeypatch):
    fake, _ = _fake_client({"choices": []})
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.api.ai.httpx.AsyncClient", fake)

    response = await client.post("/api/v1/ai/chat", json={"message": "What is inflation?"})

    assert "I can help you with" in response.json()["response"]


async def test_banking_intent_never_calls_llm(client, monkeypatch):
    fake, calls = _fake_client({"choices": [{"message": {"content": "invented"}}]})
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr("app.api.ai.httpx.AsyncClient", fake)

    response = await client.post("/api/v1/ai/chat", json={"message": "show my balance"})

    assert response.json()["tool_used"] == "get_account_balance"
    assert calls == []


async def test_empty_message_is_rejected(client):
    response = await client.post("/api/v1/ai/chat", json={"message": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Message cannot be empty"


async def test_conversation_history_is_kept_and_listed(client):
    first = await client.post("/api/v1/ai/chat", json={"message": "show my balance"})
    conversation_id = first.json()["conversation_id"]
    second = await client.post(
        "/api/v1/ai/chat", json={"message": "and my profile?", "conversation_id": conversation_id}
    )

    conversations = await client.get("/api/v1/ai/conversations")
    messages = await client.get(f"/api/v1/ai/conversations/{conversation_id}")

    assert second.json()["conversation_id"] == conversation_id
    assert [c["id"] for c in conversations.json()] == [conversation_id]
    assert conversations.json()[0]["title"] == "show my balance"
    roles = [m["role"] for m in messages.json()]
    assert roles == ["user", "assistant", "user", "assistant"]
    assert messages.json()[1]["tool_name"] == "get_account_balance"


async def test_unknown_conversation_id_starts_a_new_conversation(client):
    unknown = str(uuid.uuid4())

    response = await client.post("/api/v1/ai/chat", json={"message": "hello", "conversation_id": unknown})

    assert response.status_code == 200
    assert response.json()["conversation_id"] != unknown


async def test_unknown_conversation_messages_return_404(client):
    response = await client.get(f"/api/v1/ai/conversations/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"
