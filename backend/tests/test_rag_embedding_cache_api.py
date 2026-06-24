from fastapi.testclient import TestClient

from app.main import app


def test_refresh_embedding_cache_api_returns_runtime_summary(monkeypatch):
    monkeypatch.setattr(
        "app.api.rag_embedding_cache.refresh_embedding_cache",
        lambda mode: {
            "mode": mode,
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "knowledge_item_count": 12,
            "scanned_item_count": 12,
            "refreshed_item_count": 3,
            "missing_refreshed_count": 2,
            "stale_refreshed_count": 1,
            "error_count": 0,
            "elapsed_ms": 184,
        },
    )

    client = TestClient(app)
    response = client.post("/api/rag/embedding-cache/refresh", json={"mode": "missing"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "missing"
    assert payload["refreshed_item_count"] == 3
    assert payload["missing_refreshed_count"] == 2
    assert payload["stale_refreshed_count"] == 1


def test_refresh_embedding_cache_api_rejects_invalid_mode():
    client = TestClient(app)
    response = client.post("/api/rag/embedding-cache/refresh", json={"mode": "invalid"})

    assert response.status_code == 422
