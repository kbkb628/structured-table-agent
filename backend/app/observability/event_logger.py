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
from app.storage.analysis_store import list_task_events
from app.storage.analysis_store import record_event


def record_analysis_event(task_id: str, event_type: str, node: str, message: str, payload: dict) -> dict:
    return record_event(task_id, event_type, node, message, payload)


def list_analysis_events(task_id: str) -> list[dict]:
    return list_task_events(task_id)


def hydrate_state_events(state: dict) -> dict:
    state["events"] = list_analysis_events(state["task_id"])
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
    return record_analysis_event(task_id, FIELDS_MATCHED, "match_fields", "matched analysis fields", payload)


def record_tool_called(task_id: str, tool_name: str, payload: dict) -> dict:
    return record_analysis_event(task_id, TOOL_CALLED, tool_name, f"calling {tool_name}", payload)


def record_tool_succeeded(task_id: str, tool_name: str, payload: dict) -> dict:
    return record_analysis_event(task_id, TOOL_SUCCEEDED, tool_name, f"{tool_name} succeeded", payload)


def record_tool_failed(task_id: str, tool_name: str, payload: dict) -> dict:
    return record_analysis_event(task_id, TOOL_FAILED, tool_name, f"{tool_name} failed", payload)


def record_chart_generated(task_id: str, payload: dict) -> dict:
    return record_analysis_event(task_id, CHART_GENERATED, "generate_chart", "generated bar chart", payload)


def record_chart_failed(task_id: str, payload: dict) -> dict:
    return record_analysis_event(task_id, CHART_FAILED, "generate_chart", "chart generation degraded", payload)


def record_report_generated(task_id: str, payload: dict) -> dict:
    return record_analysis_event(task_id, REPORT_GENERATED, "generate_report", "generated final report", payload)


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
