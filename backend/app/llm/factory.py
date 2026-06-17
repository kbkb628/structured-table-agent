import os

from app.core import config
from app.llm.mock_client import MockLLMClient
from app.llm.qwen_client import QwenClient


class LLMConfigurationError(RuntimeError):
    pass


def _resolve_api_key() -> str | None:
    explicit_key = (
        os.getenv("QWEN_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or config.get_env("QWEN_API_KEY")
        or config.get_env("DASHSCOPE_API_KEY")
    )
    if explicit_key:
        return explicit_key

    compatible_key_names = sorted(
        name for name in os.environ if name.startswith("OPENAI_API_KEY")
    )
    for name in compatible_key_names:
        value = os.getenv(name)
        if value:
            return value
    return None


def get_llm_client():
    provider = (os.getenv("LLM_PROVIDER") or config.get_env("LLM_PROVIDER", "qwen") or "qwen").strip().lower()
    allow_fallback = (os.getenv("LLM_ALLOW_FALLBACK") or str(config.get_bool_env("LLM_ALLOW_FALLBACK", False))).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    api_key = _resolve_api_key()

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
        base_url=os.getenv("QWEN_BASE_URL") or config.get_env("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1") or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model=os.getenv("QWEN_MODEL") or config.get_env("QWEN_MODEL", "qwen-plus") or "qwen-plus",
        timeout_seconds=float(os.getenv("QWEN_TIMEOUT_SECONDS") or config.get_float_env("QWEN_TIMEOUT_SECONDS", 30.0)),
    )
