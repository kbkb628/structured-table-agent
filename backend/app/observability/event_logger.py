from app.observability.trace_models import DATASET_PROFILED
from app.observability.trace_models import CHART_FAILED
from app.observability.trace_models import CHART_GENERATED
from app.observability.trace_models import EVAL_FINISHED
from app.observability.trace_models import FIELDS_MATCHED
from app.observability.trace_models import GOAL_UNDERSTOOD
from app.observability.trace_models import PLAN_GENERATED
from app.observability.trace_models import RAG_RETRIEVED
from app.observability.trace_models import REPORT_GENERATED
from app.observability.trace_models import TASK_COMPLETED
from app.observability.trace_models import TASK_CREATED
from app.observability.trace_models import TASK_FAILED
from app.observability.trace_models import TOOL_CALLED
from app.observability.trace_models import TOOL_FAILED
from app.observability.trace_models import TOOL_SUCCEEDED
from app.storage.analysis_store import backfill_task_events
from app.storage.analysis_store import list_task_events
from app.storage.analysis_store import record_event


def record_analysis_event(task_id: str, event_type: str, node: str, message: str, payload: dict) -> dict:
    return record_event(task_id, event_type, node, message, payload)


def _summarize_tool_request(payload: dict) -> dict:
    return {
        "input_keys": sorted(payload.keys()),
        "group_by": payload.get("group_by"),
        "metric_column": payload.get("metric_column"),
        "aggregation": payload.get("aggregation"),
        "limit": payload.get("limit"),
        "row_count": len(payload.get("rows", [])) if isinstance(payload.get("rows"), list) else 0,
    }


def _retry_summary(payload: dict) -> dict:
    metadata = payload.get("metadata") or {}
    return {
        "retry_attempts": metadata.get("retry_attempts", 0),
        "retry_status": metadata.get("retry_status", "not_needed"),
    }


def _summarize_tool_response(payload: dict) -> dict:
    rows = (payload.get("data") or {}).get("rows") or []
    error = payload.get("error") or {}
    metadata = payload.get("metadata") or {}
    return {
        "output_keys": sorted(payload.keys()),
        "success": payload.get("success"),
        "row_count": len(rows),
        "metric_label": payload.get("metric_label"),
        "error_code": error.get("code"),
        "summary": payload.get("summary", ""),
        **_retry_summary(payload),
    }


def _summarize_field_match(payload: dict) -> dict:
    return {
        "dimension_field": payload.get("dimension_field"),
        "metric_count": len(payload.get("metrics", [])),
        "planned_tool_call_count": len(payload.get("planned_tool_calls", [])),
        "warning_count": len(payload.get("warnings", [])),
    }


def _summarize_report(payload: dict) -> dict:
    return {
        "title": payload.get("title"),
        "analysis_goal": payload.get("analysis_goal"),
        "key_findings_count": len(payload.get("key_findings", [])),
        "chart_count": len(payload.get("chart_specs", [])),
    }


def list_analysis_events(task_id: str) -> list[dict]:
    return list_task_events(task_id)


def hydrate_state_events(state: dict) -> dict:
    if state.get("events"):
        backfill_task_events(state["task_id"], state["events"])
    persisted_events = list_analysis_events(state["task_id"])
    if persisted_events or not state.get("events"):
        state["events"] = persisted_events
    return state


def record_startup_events(
    task_id: str,
    node: str,
    file_profile: dict,
    business_context: list[dict],
    analysis_goal: str,
    analysis_plan: list[str],
) -> None:
    record_analysis_event(task_id, TASK_CREATED, node, "task created", {"status": "created"})
    record_analysis_event(
        task_id,
        DATASET_PROFILED,
        node,
        "dataset profile prepared",
        {
            "filename": file_profile.get("filename"),
            "row_count": file_profile.get("row_count"),
            "column_count": file_profile.get("column_count"),
            "column_names": [item["name"] for item in file_profile.get("columns", [])],
        },
    )
    record_analysis_event(
        task_id,
        RAG_RETRIEVED,
        node,
        "business context retrieved",
        {"item_count": len(business_context), "item_ids": [item["id"] for item in business_context]},
    )
    record_analysis_event(
        task_id,
        GOAL_UNDERSTOOD,
        node,
        "analysis goal generated",
        {"analysis_goal": analysis_goal},
    )
    record_analysis_event(
        task_id,
        PLAN_GENERATED,
        node,
        "analysis plan generated",
        {"analysis_plan": analysis_plan},
    )


def record_fields_matched(task_id: str, payload: dict) -> dict:
    enriched_payload = {
        **payload,
        "node_input_summary": {
            "candidate_field_count": len(payload.get("candidate_fields", [])),
        },
        "node_output_summary": _summarize_field_match(payload),
        "tool_result_summary": {
            "dimension_field": payload.get("dimension_field"),
            "metric_count": len(payload.get("metrics", [])),
        },
    }
    return record_analysis_event(task_id, FIELDS_MATCHED, "match_fields", "matched analysis fields", enriched_payload)


def record_tool_called(task_id: str, tool_name: str, payload: dict) -> dict:
    tool_summary = {"tool_name": tool_name, "status": "called", **_retry_summary(payload)}
    enriched_payload = {
        **payload,
        "node_input_summary": _summarize_tool_request(payload),
        "node_output_summary": {"status": "pending"},
        "tool_result_summary": tool_summary,
    }
    return record_analysis_event(task_id, TOOL_CALLED, tool_name, f"calling {tool_name}", enriched_payload)


def record_tool_succeeded(task_id: str, tool_name: str, payload: dict) -> dict:
    tool_summary = _summarize_tool_response(payload)
    retry_summary = _retry_summary(payload)
    enriched_payload = {
        **payload,
        "node_input_summary": {
            "tool_name": tool_name,
            "metric_label": payload.get("metric_label"),
        },
        "node_output_summary": tool_summary,
        "tool_result_summary": {**tool_summary, **retry_summary},
    }
    return record_analysis_event(task_id, TOOL_SUCCEEDED, tool_name, f"{tool_name} succeeded", enriched_payload)


def record_tool_failed(task_id: str, tool_name: str, payload: dict) -> dict:
    tool_summary = _summarize_tool_response(payload)
    retry_summary = _retry_summary(payload)
    enriched_payload = {
        **payload,
        "node_input_summary": {
            "tool_name": tool_name,
            "metric_label": payload.get("metric_label"),
        },
        "node_output_summary": tool_summary,
        "tool_result_summary": {**tool_summary, **retry_summary},
    }
    return record_analysis_event(task_id, TOOL_FAILED, tool_name, f"{tool_name} failed", enriched_payload)


def record_chart_generated(task_id: str, payload: dict) -> dict:
    return record_analysis_event(task_id, CHART_GENERATED, "generate_chart", "generated bar chart", payload)


def record_chart_failed(task_id: str, payload: dict) -> dict:
    return record_analysis_event(task_id, CHART_FAILED, "generate_chart", "chart generation degraded", payload)


def record_report_generated(task_id: str, payload: dict) -> dict:
    enriched_payload = {
        **payload,
        "node_input_summary": {
            "title": payload.get("title"),
            "analysis_goal": payload.get("analysis_goal"),
        },
        "node_output_summary": _summarize_report(payload),
        "tool_result_summary": _summarize_report(payload),
    }
    return record_analysis_event(task_id, REPORT_GENERATED, "generate_report", "generated final report", enriched_payload)


def record_task_completed(task_id: str, node: str) -> dict:
    return record_analysis_event(task_id, TASK_COMPLETED, node, "analysis task completed", {"status": "completed"})


def record_task_failed(task_id: str, node: str, message: str, payload: dict) -> dict:
    return record_analysis_event(task_id, TASK_FAILED, node, message, payload)


def record_eval_finished(task_id: str, node: str, payload: dict) -> dict:
    return record_analysis_event(task_id, EVAL_FINISHED, node, "rule evaluation completed", payload)


def record_session_store_warning(task_id: str, payload: dict) -> dict:
    return record_analysis_event(
        task_id,
        "session_store_warning",
        "session_store",
        "session store downgraded to SQLite",
        payload,
    )


def record_session_state_recovered(task_id: str, payload: dict) -> dict:
    return record_analysis_event(
        task_id,
        "session_state_recovered",
        "session_store",
        "session state recovered from granular Redis keys",
        payload,
    )
