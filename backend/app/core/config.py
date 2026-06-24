import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "samples"
DB_PATH = BASE_DIR / "app.db"
KNOWLEDGE_BASE_PATH = BASE_DIR / "app" / "rag" / "knowledge_base.jsonl"


def get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def get_bool_env(name: str, default: bool = False) -> bool:
    fallback = "true" if default else "false"
    return (get_env(name, fallback) or fallback).strip().lower() in {"1", "true", "yes", "on"}


def get_float_env(name: str, default: float) -> float:
    raw_value = get_env(name, str(default))
    return float(raw_value if raw_value is not None else default)


RAG_BI_ENCODER_MODEL = get_env("RAG_BI_ENCODER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
RAG_RERANK_MODEL = get_env("RAG_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RAG_BM25_TOP_K = int(get_env("RAG_BM25_TOP_K", "8") or "8")
RAG_VECTOR_TOP_K = int(get_env("RAG_VECTOR_TOP_K", "8") or "8")
RAG_FINAL_TOP_K = int(get_env("RAG_FINAL_TOP_K", "5") or "5")
RAG_ENABLE_VECTOR_RETRIEVAL = get_bool_env("RAG_ENABLE_VECTOR_RETRIEVAL", True)
RAG_ENABLE_RERANK = get_bool_env("RAG_ENABLE_RERANK", True)
MEMORY_ENABLED = get_bool_env("MEMORY_ENABLED", True)
MEMORY_MAX_RECENT_TURNS = int(get_env("MEMORY_MAX_RECENT_TURNS", "3") or "3")
MEMORY_SUMMARY_MAX_CHARS = int(get_env("MEMORY_SUMMARY_MAX_CHARS", "480") or "480")
DOCKER_SANDBOX_ENABLED = get_bool_env("DOCKER_SANDBOX_ENABLED", True)
DOCKER_SANDBOX_IMAGE = get_env("DOCKER_SANDBOX_IMAGE", "python:3.12-slim") or "python:3.12-slim"
DOCKER_SANDBOX_TIMEOUT_SECONDS = int(get_env("DOCKER_SANDBOX_TIMEOUT_SECONDS", "8") or "8")
DOCKER_SANDBOX_MEMORY_MB = int(get_env("DOCKER_SANDBOX_MEMORY_MB", "256") or "256")
DOCKER_SANDBOX_CPU_LIMIT = get_env("DOCKER_SANDBOX_CPU_LIMIT", "1.0") or "1.0"
DOCKER_SANDBOX_NETWORK_DISABLED = get_bool_env("DOCKER_SANDBOX_NETWORK_DISABLED", True)
DOCKER_SANDBOX_TMP_ROOT = DATA_DIR / "sandbox_runs"
