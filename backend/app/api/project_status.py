from fastapi import APIRouter

from app.llm.factory import describe_llm_provider_diagnostics
from app.llm.factory import describe_llm_provider_resolution
from app.storage.database import get_connection
from app.storage.database import init_db

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
