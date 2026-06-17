import uuid

from app.observability.event_logger import hydrate_state_events
from app.observability.event_logger import list_analysis_events
from app.observability.event_logger import record_eval_finished
from app.observability.event_logger import record_startup_events
from app.observability.event_logger import record_task_completed
from app.storage.analysis_store import create_task


def _build_state(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "file_id": "file_001",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": ["match fields", "aggregate sales"],
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }


def test_record_startup_events_writes_expected_trace_sequence():
    state = _build_state(f"task_event_startup_{uuid.uuid4().hex[:8]}")
    create_task(state["task_id"], state["file_id"], state["question"], state)

    record_startup_events(
        state["task_id"],
        "start_analysis",
        [{"id": "metric_sales_amount"}, {"id": "dimension_region"}],
        "compare region sales",
        ["match fields", "aggregate sales"],
    )

    events = list_analysis_events(state["task_id"])

    assert [event["event_type"] for event in events] == [
        "task_created",
        "rag_retrieved",
        "goal_understood",
        "plan_generated",
    ]
    assert events[1]["payload"]["item_count"] == 2
    assert events[1]["payload"]["item_ids"] == ["metric_sales_amount", "dimension_region"]


def test_hydrate_state_events_loads_latest_persisted_events():
    state = _build_state(f"task_event_hydrate_{uuid.uuid4().hex[:8]}")
    create_task(state["task_id"], state["file_id"], state["question"], state)

    record_startup_events(
        state["task_id"],
        "eval_cases",
        [{"id": "metric_sales_amount"}],
        state["analysis_goal"],
        state["analysis_plan"],
    )
    record_task_completed(state["task_id"], "langgraph")
    record_eval_finished(state["task_id"], "run_eval", {"overall_score": 1.0})

    hydrate_state_events(state)

    assert len(state["events"]) == 6
    assert state["events"][-2]["event_type"] == "task_completed"
    assert state["events"][-1]["event_type"] == "eval_finished"
    assert state["events"][-1]["payload"]["overall_score"] == 1.0
