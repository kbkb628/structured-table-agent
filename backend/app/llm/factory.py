import os

from app.core import config
from app.llm.mock_client import MockLLMClient
from app.llm.qwen_client import QwenClient


class LLMConfigurationError(RuntimeError):
    pass


def _resolve_api_key() -> tuple[str | None, str | None]:
    explicit_key = (
        os.getenv("QWEN_API_KEY")
    )
    if explicit_key:
        return explicit_key, "QWEN_API_KEY"

    dashscope_key = (
        os.getenv("DASHSCOPE_API_KEY")
        or config.get_env("DASHSCOPE_API_KEY")
    )
    if dashscope_key:
        return dashscope_key, "DASHSCOPE_API_KEY"

    configured_qwen_key = config.get_env("QWEN_API_KEY")
    if configured_qwen_key:
        return configured_qwen_key, "QWEN_API_KEY"

    compatible_key_names = sorted(
        name for name in os.environ if name.startswith("OPENAI_API_KEY")
    )
    for name in compatible_key_names:
        value = os.getenv(name)
        if value:
            return value, name
    return None, None


def describe_llm_provider_resolution() -> dict:
    provider = (os.getenv("LLM_PROVIDER") or config.get_env("LLM_PROVIDER", "qwen") or "qwen").strip().lower()
    allow_fallback = (os.getenv("LLM_ALLOW_FALLBACK") or str(config.get_bool_env("LLM_ALLOW_FALLBACK", False))).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    api_key, api_key_source = _resolve_api_key()
    return {
        "provider": provider,
        "allow_fallback": allow_fallback,
        "has_api_key": bool(api_key),
        "api_key_source": api_key_source,
        "base_url": os.getenv("QWEN_BASE_URL") or config.get_env("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1") or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": os.getenv("QWEN_MODEL") or config.get_env("QWEN_MODEL", "qwen-plus") or "qwen-plus",
        "timeout_seconds": float(os.getenv("QWEN_TIMEOUT_SECONDS") or config.get_float_env("QWEN_TIMEOUT_SECONDS", 30.0)),
    }


def get_llm_client():
    resolution = describe_llm_provider_resolution()
    provider = resolution["provider"]
    allow_fallback = resolution["allow_fallback"]
    api_key = _resolve_api_key()[0]

    if provider == "mock":
        return MockLLMClient()

    if provider != "qwen":
        raise LLMConfigurationError(f"Unsupported LLM provider: {provider}")

    if not api_key:
        if allow_fallback:
            return MockLLMClient()
        raise LLMConfigurationError(
            "A Qwen-compatible API key is required when LLM_PROVIDER=qwen. "
            "Set QWEN_API_KEY, DASHSCOPE_API_KEY, or an OPENAI_API_KEY* environment variable."
        )

    return QwenClient(
        api_key=api_key,
        api_key_source=resolution["api_key_source"],
        base_url=resolution["base_url"],
        model=resolution["model"],
        timeout_seconds=resolution["timeout_seconds"],
    )
