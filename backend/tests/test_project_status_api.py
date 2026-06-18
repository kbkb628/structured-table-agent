from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.storage.session_store import SessionStore


def test_get_project_status_reports_current_counters(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "test-key")

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["provider"]["provider"] == "qwen"
    assert payload["summary"]["provider"]["diagnostics"]["smoke_ready"] is True
    assert payload["summary"]["demo"]["available"] is True
    assert payload["summary"]["session_store"]["preferred_backend"] == "redis"
    assert payload["summary"]["database"]["tables"]
    assert "analysis_tasks" in payload["summary"]["database"]["tables"]
    assert "analysis_events" in payload["summary"]["database"]["tables"]


def test_get_project_status_includes_live_counts():
    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["database"]["tables"]["analysis_tasks"]["exists"] is True
    assert payload["summary"]["database"]["tables"]["analysis_events"]["exists"] is True
    assert payload["summary"]["database"]["tables"]["tool_call_logs"]["exists"] is True
    assert payload["summary"]["database"]["tables"]["eval_results"]["exists"] is True
    assert payload["summary"]["session_store"]["degraded_to_sqlite"] is True


def test_get_project_status_reports_redis_session_store_when_available(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://fake-redis:6379/0")
    client = TestClient(app)

    with patch.object(SessionStore, "_connect", lambda self: object()):
        response = client.get("/api/project-status")

    assert response.status_code == 200
    payload = response.json()
    session_store = payload["summary"]["session_store"]
    assert session_store["preferred_backend"] == "redis"
    assert session_store["active_backend"] == "redis"
    assert session_store["redis_available"] is True
    assert session_store["degraded_to_sqlite"] is False
