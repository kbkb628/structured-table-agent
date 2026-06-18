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
            ORDER BY created_at DESC, rowid DESC
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
            SELECT task_id, created_at, payload_json
            FROM analysis_events
            WHERE event_type = ?
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """,
            ("session_state_recovered",),
        ).fetchone()
    latest_recovered_payload = json.loads(latest_recovered[2]) if latest_recovered and latest_recovered[2] else {}
    latest_recovered_segments = latest_recovered_payload.get("recovered_segments") or []
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
            "latest_recovered_recovery_source": latest_recovered_payload.get("recovery_source"),
            "latest_recovered_segment_count": len(latest_recovered_segments),
            "latest_recovered_segments": latest_recovered_segments,
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
    suggestions = eval_result.get("suggestions") if isinstance(eval_result.get("suggestions"), list) else []
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
    top_business_context = business_context[0] if business_context else {}
    top_business_context_score_breakdown = top_business_context.get("score_breakdown") or {}
    field_understanding = state.get("field_understanding") or {}
    metrics = field_understanding.get("metrics") or []
    completed_steps = state.get("completed_steps") or []
    route_decisions = [
        step.split("route_next_step:", 1)[1]
        for step in completed_steps
        if isinstance(step, str) and step.startswith("route_next_step:")
    ]
    intermediate_findings = state.get("intermediate_findings") or []
    tool_results = state.get("tool_results") or []
    errors = state.get("errors") or []
    successful_tool_results = [item for item in tool_results if item.get("success") is True]
    failed_tool_results = [item for item in tool_results if item.get("success") is False]
    retried_tool_results = [
        item
        for item in tool_results
        if int((item.get("metadata") or {}).get("retry_attempts", 0) or 0) > 0
    ]
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
            "suggestion_count": len(suggestions),
            "has_dimension_scores": any(key in eval_result for key in dimension_score_keys),
            "schema_valid": eval_result.get("schema_valid"),
            "tool_success_rate": eval_result.get("tool_success_rate"),
            "tool_elapsed_ms_total": eval_result.get("tool_elapsed_ms_total"),
            "field_validity": eval_result.get("field_validity"),
            "chart_validity": eval_result.get("chart_validity"),
            "report_completeness": eval_result.get("report_completeness"),
            "trace_completeness": eval_result.get("trace_completeness"),
        },
        "judgement": {
            "supported_by_tools": llm_judgement.get("supported_by_tools"),
            "has_findings": llm_judgement.get("has_findings"),
            "issue_count": int(llm_judgement.get("issue_count", 0) or 0),
        },
        "process": {
            "pending_metric_count": len(state.get("pending_metrics") or []),
            "planned_tool_call_count": len(state.get("pending_tool_calls") or []),
            "event_count": int(event_count[0]) if event_count else 0,
            "latest_event_type": latest_event[0] if latest_event else None,
            "latest_event_at": latest_event[1] if latest_event else None,
            "llm_issue_count": int(llm_judgement.get("issue_count", 0) or 0),
            "route_decision_count": len(route_decisions),
            "continued_route_decision_count": sum(1 for item in route_decisions if item == "continue"),
            "finished_route_decision_count": sum(1 for item in route_decisions if item == "finish"),
            "latest_route_decision": route_decisions[-1] if route_decisions else None,
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
            "top_business_context_title": top_business_context.get("title"),
            "top_business_context_score": top_business_context.get("score"),
            "top_business_context_related_field_count": len(top_business_context.get("related_fields") or []),
            "top_business_context_has_score_breakdown": bool(top_business_context_score_breakdown),
            "top_business_context_keyword_score": top_business_context_score_breakdown.get("keyword_score"),
            "top_business_context_field_score": top_business_context_score_breakdown.get("field_score"),
            "top_business_context_phrase_score": top_business_context_score_breakdown.get("phrase_score"),
            "top_business_context_bm25_score": top_business_context_score_breakdown.get("bm25_score"),
            "checkpoint_current_step": context_checkpoint.get("current_step"),
            "checkpoint_status": context_checkpoint.get("status"),
            "checkpoint_pending_metric_count": context_checkpoint.get("pending_metric_count"),
            "checkpoint_finding_count": context_checkpoint.get("finding_count"),
            "checkpoint_business_context_title_count": len(context_checkpoint.get("business_context_titles") or []),
            "checkpoint_business_context_titles": context_checkpoint.get("business_context_titles") or [],
            "checkpoint_draft_report_status": context_checkpoint.get("draft_report_status"),
            "checkpoint_latest_error_code": context_checkpoint.get("latest_error_code", ""),
        },
        "semantics": {
            "analysis_goal": state.get("analysis_goal"),
            "analysis_plan_count": len(state.get("analysis_plan") or []),
            "current_step": state.get("current_step"),
            "completed_step_count": len(completed_steps),
            "finding_count": len(intermediate_findings),
            "dimension_field": field_understanding.get("dimension_field"),
            "match_analysis_type": field_understanding.get("analysis_type"),
            "candidate_field_count": len(field_understanding.get("candidate_fields") or []),
            "match_warning_count": len(field_understanding.get("warnings") or []),
            "planned_tool_sequence": field_understanding.get("planned_tool_sequence") or [],
            "metric_count": (
                len(metrics)
                if metrics
                else (
                    len(state.get("pending_metrics") or [])
                    if state.get("pending_metrics")
                    else (1 if field_understanding.get("metric_field") else 0)
                )
            ),
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
            "retried_tool_result_count": len(retried_tool_results),
            "retry_attempts_total": sum(
                int((item.get("metadata") or {}).get("retry_attempts", 0) or 0)
                for item in tool_results
            ),
            "latest_tool_name": (
                latest_tool_log[0]
                if latest_tool_log
                else (tool_results[-1].get("tool_name") if tool_results else None)
            ),
            "latest_retry_status": (
                (tool_results[-1].get("metadata") or {}).get("retry_status")
                if tool_results
                else None
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
