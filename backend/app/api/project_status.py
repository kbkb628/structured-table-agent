import os
import json

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
    init_db()
    with get_connection() as conn:
        warning_count = conn.execute(
            "SELECT COUNT(*) FROM analysis_events WHERE event_type = ?",
            ("session_store_warning",),
        ).fetchone()
        latest_warning = conn.execute(
            """
            SELECT task_id, created_at
            FROM analysis_events
            WHERE event_type = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            ("session_store_warning",),
        ).fetchone()
        recovered_count = conn.execute(
            "SELECT COUNT(*) FROM analysis_events WHERE event_type = ?",
            ("session_state_recovered",),
        ).fetchone()
        latest_recovered = conn.execute(
            """
            SELECT task_id, created_at
            FROM analysis_events
            WHERE event_type = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            ("session_state_recovered",),
        ).fetchone()
    return {
        "preferred_backend": "redis",
        "active_backend": "redis" if redis_available else "sqlite",
        "redis_available": redis_available,
        "degraded_to_sqlite": not redis_available,
        "redis_url": redis_url,
        "event_summary": {
            "warning_count": int(warning_count[0]) if warning_count else 0,
            "recovered_count": int(recovered_count[0]) if recovered_count else 0,
            "latest_warning_task_id": latest_warning[0] if latest_warning else None,
            "latest_warning_at": latest_warning[1] if latest_warning else None,
            "latest_recovered_task_id": latest_recovered[0] if latest_recovered else None,
            "latest_recovered_at": latest_recovered[1] if latest_recovered else None,
        },
    }


def _latest_task_info() -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT task_id, status, state_json, updated_at
            FROM analysis_tasks
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        task_id, status, state_json, updated_at = row
        state = json.loads(state_json)
        tool_log_count = conn.execute(
            "SELECT COUNT(*) FROM tool_call_logs WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        latest_tool_log = conn.execute(
            """
            SELECT tool_name
            FROM tool_call_logs
            WHERE task_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
        event_count = conn.execute(
            "SELECT COUNT(*) FROM analysis_events WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        latest_event = conn.execute(
            """
            SELECT event_type, created_at
            FROM analysis_events
            WHERE task_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
    eval_result = state.get("eval_result") or {}
    issues = eval_result.get("issues") if isinstance(eval_result.get("issues"), list) else []
    dimension_score_keys = {
        "schema_valid",
        "tool_success_rate",
        "field_validity",
        "chart_validity",
        "report_completeness",
        "trace_completeness",
    }
    llm_judgement = state.get("llm_judgement") or {}
    final_report = state.get("final_report") or {}
    chart_specs = state.get("chart_specs") or []
    context_checkpoint = state.get("context_checkpoint") or {}
    business_context = state.get("business_context") or []
    tool_results = state.get("tool_results") or []
    errors = state.get("errors") or []
    successful_tool_results = [item for item in tool_results if item.get("success") is True]
    failed_tool_results = [item for item in tool_results if item.get("success") is False]
    latest_error = errors[-1] if errors else {}
    return {
        "task_id": task_id,
        "status": status,
        "updated_at": updated_at,
        "artifacts": {
            "has_business_context": bool(state.get("business_context")),
            "has_context_checkpoint": bool(state.get("context_checkpoint")),
            "has_draft_report": bool(state.get("draft_report")),
            "has_final_report": bool(state.get("final_report")),
            "has_llm_judgement": bool(state.get("llm_judgement")),
            "tool_call_log_count": int(tool_log_count[0]) if tool_log_count else 0,
        },
        "evaluation": {
            "has_eval_result": bool(eval_result),
            "overall_score": eval_result.get("overall_score"),
            "issue_count": len(issues),
            "has_dimension_scores": any(key in eval_result for key in dimension_score_keys),
        },
        "process": {
            "pending_metric_count": len(state.get("pending_metrics") or []),
            "planned_tool_call_count": len(state.get("pending_tool_calls") or []),
            "event_count": int(event_count[0]) if event_count else 0,
            "latest_event_type": latest_event[0] if latest_event else None,
            "latest_event_at": latest_event[1] if latest_event else None,
            "llm_issue_count": int(llm_judgement.get("issue_count", 0) or 0),
        },
        "report": {
            "chart_spec_count": len(chart_specs),
            "key_finding_count": len(final_report.get("key_findings") or []),
            "business_suggestion_count": len(final_report.get("business_suggestions") or []),
            "data_limitation_count": len(final_report.get("data_limitations") or []),
            "next_step_count": len(final_report.get("next_steps") or []),
        },
        "context": {
            "business_context_count": len(business_context),
            "top_business_context_title": business_context[0].get("title") if business_context else None,
            "checkpoint_current_step": context_checkpoint.get("current_step"),
            "checkpoint_draft_report_status": context_checkpoint.get("draft_report_status"),
            "checkpoint_latest_error_code": context_checkpoint.get("latest_error_code", ""),
        },
        "errors": {
            "error_count": len(errors),
            "latest_error_code": latest_error.get("code"),
            "latest_error_message": latest_error.get("message"),
            "has_degradation": any(
                isinstance(item, dict) and "DEGRADE" in str(item.get("code") or "").upper()
                for item in errors
            ),
        },
        "tools": {
            "tool_result_count": len(tool_results),
            "successful_tool_result_count": len(successful_tool_results),
            "failed_tool_result_count": len(failed_tool_results),
            "total_tool_elapsed_ms": sum(
                int((item.get("metadata") or {}).get("elapsed_ms", 0))
                for item in tool_results
            ),
            "latest_tool_name": (
                latest_tool_log[0]
                if latest_tool_log
                else (tool_results[-1].get("tool_name") if tool_results else None)
            ),
        },
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
            "latest_task": _latest_task_info(),
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
