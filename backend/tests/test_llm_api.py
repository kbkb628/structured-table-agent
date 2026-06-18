from fastapi.testclient import TestClient

from app.main import app


def test_get_llm_provider_status_reports_resolution(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("QWEN_MODEL", "qwen-plus")
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "test-key")

    client = TestClient(app)
    response = client.get("/api/llm/provider-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "qwen"
    assert payload["allow_fallback"] is False
    assert payload["has_api_key"] is True
    assert payload["api_key_source"] == "OPENAI_API_KEY_0011AI"
    assert payload["model"] == "qwen-plus"
    assert payload["base_url"].startswith("https://")


def test_post_llm_provider_smoke_returns_runtime_failure_details(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "test-key")

    class FailingClient:
        def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
            del question
            del file_profile
            del business_context
            raise RuntimeError("provider smoke failed")

    monkeypatch.setattr("app.api.llm.get_llm_client", lambda: FailingClient())

    client = TestClient(app)
    response = client.post("/api/llm/provider-smoke")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is False
    assert payload["client_type"] == "FailingClient"
    assert payload["provider_resolution"]["api_key_source"] == "OPENAI_API_KEY_0011AI"
    assert payload["error_type"] == "RuntimeError"
    assert payload["error_message"] == "provider smoke failed"


def test_post_llm_provider_smoke_returns_analysis_goal_when_provider_is_healthy(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "test-key")

    class HealthyClient:
        def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
            assert question == "analyse sales by region"
            assert file_profile["columns"][0]["name"] == "region"
            assert business_context[0]["id"] == "metric_sales_amount"
            return "Compare regional sales performance"

    monkeypatch.setattr("app.api.llm.get_llm_client", lambda: HealthyClient())

    client = TestClient(app)
    response = client.post("/api/llm/provider-smoke")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["client_type"] == "HealthyClient"
    assert payload["analysis_goal"] == "Compare regional sales performance"
