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

    tongyi_key = (
        os.getenv("TONGYI_API_KEY")
        or config.get_env("TONGYI_API_KEY")
    )
    if tongyi_key:
        return tongyi_key, "TONGYI_API_KEY"

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


def describe_llm_provider_diagnostics(resolution: dict | None = None) -> dict:
    resolved = resolution or describe_llm_provider_resolution()
    provider = str(resolved.get("provider") or "").lower()
    has_api_key = bool(resolved.get("has_api_key"))
    api_key_source = resolved.get("api_key_source")
    key_source_kind = "missing"
    if api_key_source:
        key_source_kind = (
            "qwen"
            if api_key_source in {"QWEN_API_KEY", "TONGYI_API_KEY", "DASHSCOPE_API_KEY"}
            else "openai_compatible"
        )

    provider_supported = provider in {"qwen", "mock"}
    smoke_ready = provider_supported and (provider == "mock" or has_api_key)

    warnings: list[str] = []
    recommendations: list[str] = []

    if not provider_supported:
        warnings.append(f"Unsupported provider: {provider}.")
        recommendations.append("Set LLM_PROVIDER to qwen or mock.")
    if provider == "qwen" and not has_api_key:
        warnings.append("No API key was detected for qwen provider.")
        recommendations.append("Set QWEN_API_KEY, TONGYI_API_KEY, or DASHSCOPE_API_KEY before calling the real provider.")
    if provider == "qwen" and key_source_kind == "openai_compatible":
        warnings.append(f"Using compatible key source: {api_key_source}.")
        recommendations.append("If DashScope rejects the request, verify this key is a real Qwen-compatible credential.")
    if provider == "mock":
        recommendations.append("Mock provider is suitable for offline or local development runs.")

    return {
        "provider_supported": provider_supported,
        "key_source_kind": key_source_kind,
        "smoke_ready": smoke_ready,
        "warnings": warnings,
        "recommendations": recommendations,
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
            "Set QWEN_API_KEY, TONGYI_API_KEY, DASHSCOPE_API_KEY, or an OPENAI_API_KEY* environment variable."
        )

    return QwenClient(
        api_key=api_key,
        api_key_source=resolution["api_key_source"],
        base_url=resolution["base_url"],
        model=resolution["model"],
        timeout_seconds=resolution["timeout_seconds"],
    )
