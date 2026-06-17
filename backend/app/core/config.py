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
