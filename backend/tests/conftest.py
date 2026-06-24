import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.main import app


@pytest.fixture(autouse=True)
def default_llm_provider_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.delenv("LLM_ALLOW_FALLBACK", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("TONGYI_API_KEY", raising=False)
    # Keep the default test suite offline unless a test explicitly enables staged retrieval.
    monkeypatch.setattr(config, "RAG_ENABLE_VECTOR_RETRIEVAL", False)
    monkeypatch.setattr(config, "RAG_ENABLE_RERANK", False)


def create_client() -> TestClient:
    return TestClient(app)
