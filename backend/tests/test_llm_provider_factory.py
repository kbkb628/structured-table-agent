import pytest


def _clear_compatible_key_env(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("TONGYI_API_KEY", raising=False)
    for name in list(__import__("os").environ):
        if name.startswith("OPENAI_API_KEY"):
            monkeypatch.delenv(name, raising=False)


def test_get_llm_client_returns_mock_when_provider_is_mock(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    from app.llm.factory import get_llm_client
    from app.llm.mock_client import MockLLMClient

    client = get_llm_client()

    assert isinstance(client, MockLLMClient)


def test_get_llm_client_returns_qwen_when_provider_is_qwen(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("QWEN_API_KEY", "test-key")

    from app.llm.factory import get_llm_client
    from app.llm.qwen_client import QwenClient

    client = get_llm_client()

    assert isinstance(client, QwenClient)


def test_get_llm_client_raises_when_qwen_key_is_missing(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    _clear_compatible_key_env(monkeypatch)

    from app.llm.factory import LLMConfigurationError, get_llm_client

    with pytest.raises(LLMConfigurationError):
        get_llm_client()


def test_get_llm_client_falls_back_to_mock_when_enabled(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("LLM_ALLOW_FALLBACK", "true")
    _clear_compatible_key_env(monkeypatch)

    from app.llm.factory import get_llm_client
    from app.llm.mock_client import MockLLMClient

    client = get_llm_client()

    assert isinstance(client, MockLLMClient)


def test_get_llm_client_accepts_custom_openai_compatible_key_name(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    _clear_compatible_key_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "test-key")

    from app.llm.factory import get_llm_client
    from app.llm.qwen_client import QwenClient

    client = get_llm_client()

    assert isinstance(client, QwenClient)
    assert client.api_key == "test-key"
    assert client.api_key_source == "OPENAI_API_KEY_0011AI"


def test_get_llm_client_prefers_tongyi_api_key_over_openai_compatible_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    _clear_compatible_key_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "wrong-key")
    monkeypatch.setenv("TONGYI_API_KEY", "tongyi-key")

    from app.llm.factory import get_llm_client
    from app.llm.qwen_client import QwenClient

    client = get_llm_client()

    assert isinstance(client, QwenClient)
    assert client.api_key == "tongyi-key"
    assert client.api_key_source == "TONGYI_API_KEY"


def test_describe_llm_provider_resolution_reports_key_source(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("QWEN_MODEL", "qwen-plus")
    _clear_compatible_key_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "test-key")

    from app.llm.factory import describe_llm_provider_resolution

    resolution = describe_llm_provider_resolution()

    assert resolution["provider"] == "qwen"
    assert resolution["has_api_key"] is True
    assert resolution["api_key_source"] == "OPENAI_API_KEY_0011AI"
    assert resolution["model"] == "qwen-plus"


def test_describe_llm_provider_resolution_reports_tongyi_key_source(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("QWEN_MODEL", "qwen-plus")
    _clear_compatible_key_env(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "wrong-key")
    monkeypatch.setenv("TONGYI_API_KEY", "tongyi-key")

    from app.llm.factory import describe_llm_provider_resolution

    resolution = describe_llm_provider_resolution()

    assert resolution["provider"] == "qwen"
    assert resolution["has_api_key"] is True
    assert resolution["api_key_source"] == "TONGYI_API_KEY"
