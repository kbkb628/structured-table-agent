import os

from fastapi import APIRouter

from app.llm.factory import describe_llm_provider_diagnostics
from app.llm.factory import describe_llm_provider_resolution
from app.storage.database import get_connection
from app.storage.database import init_db
from app.storage.session_store import SessionStore

router = APIRouter(tags=["project-status"])


def _table_info(table_name: str) -> dict:
    init_db()
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        if not exists:
            return {"exists": False, "row_count": 0}
        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return {"exists": True, "row_count": int(count[0]) if count else 0}


def _session_store_info() -> dict:
    redis_url = os.getenv("REDIS_URL") or "redis://127.0.0.1:6379/0"
    store = SessionStore(url=redis_url)
    redis_client = store._connect()
    redis_available = redis_client is not None
    return {
        "preferred_backend": "redis",
        "active_backend": "redis" if redis_available else "sqlite",
        "redis_available": redis_available,
        "degraded_to_sqlite": not redis_available,
        "redis_url": redis_url,
    }


@router.get("/api/project-status")
def get_project_status() -> dict:
    provider_resolution = describe_llm_provider_resolution()
    provider_resolution["diagnostics"] = describe_llm_provider_diagnostics(provider_resolution)
    return {
        "summary": {
            "provider": provider_resolution,
            "demo": {
                "available": True,
                "path": "/demo",
            },
            "session_store": _session_store_info(),
            "database": {
                "tables": {
                    "files": _table_info("files"),
                    "analysis_tasks": _table_info("analysis_tasks"),
                    "analysis_events": _table_info("analysis_events"),
                    "tool_call_logs": _table_info("tool_call_logs"),
                    "eval_results": _table_info("eval_results"),
                }
            },
        }
    }
