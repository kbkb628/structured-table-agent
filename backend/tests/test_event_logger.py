import uuid

from app.observability.event_logger import hydrate_state_events
from app.observability.event_logger import list_analysis_events
from app.observability.event_logger import record_eval_finished
from app.observability.event_logger import record_startup_events
from app.observability.event_logger import record_task_completed
from app.observability.event_logger import record_tool_called
from app.observability.event_logger import record_tool_succeeded
from app.storage.analysis_store import backfill_task_events
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
        {
            "filename": "sales_orders.csv",
            "row_count": 2,
            "column_count": 3,
            "columns": [{"name": "region"}, {"name": "sales_amount"}, {"name": "order_id"}],
        },
        [{"id": "metric_sales_amount"}, {"id": "dimension_region"}],
        "compare region sales",
        ["match fields", "aggregate sales"],
    )

    events = list_analysis_events(state["task_id"])

    assert [event["event_type"] for event in events] == [
        "task_created",
        "dataset_profiled",
        "rag_retrieved",
        "goal_understood",
        "plan_generated",
    ]
    assert events[1]["payload"]["row_count"] == 2
    assert events[2]["payload"]["item_count"] == 2
    assert events[2]["payload"]["item_ids"] == ["metric_sales_amount", "dimension_region"]


def test_hydrate_state_events_loads_latest_persisted_events():
    state = _build_state(f"task_event_hydrate_{uuid.uuid4().hex[:8]}")
    create_task(state["task_id"], state["file_id"], state["question"], state)

    record_startup_events(
        state["task_id"],
        "eval_cases",
        {
            "filename": "sales_orders.csv",
            "row_count": 1,
            "column_count": 2,
            "columns": [{"name": "region"}, {"name": "sales_amount"}],
        },
        [{"id": "metric_sales_amount"}],
        state["analysis_goal"],
        state["analysis_plan"],
    )
    record_task_completed(state["task_id"], "langgraph")
    record_eval_finished(state["task_id"], "run_eval", {"overall_score": 1.0})

    hydrate_state_events(state)

    assert len(state["events"]) == 7
    assert state["events"][-2]["event_type"] == "task_completed"
    assert state["events"][-1]["event_type"] == "eval_finished"
    assert state["events"][-1]["payload"]["overall_score"] == 1.0


def test_hydrate_state_events_backfills_missing_history_into_partial_sqlite_timeline():
    task_id = f"task_event_partial_{uuid.uuid4().hex[:8]}"
    state = _build_state(task_id)
    recovered_events = [
        {
            "event_id": f"evt_{task_id}_1",
            "event_type": "task_created",
            "node": "start_analysis",
            "message": "task created",
            "payload": {"status": "created"},
            "created_at": "2026-06-18T10:00:00+00:00",
        },
        {
            "event_id": f"evt_{task_id}_2",
            "event_type": "fields_matched",
            "node": "match_fields",
            "message": "matched analysis fields",
            "payload": {"dimension_field": "region"},
            "created_at": "2026-06-18T10:00:01+00:00",
        },
        {
            "event_id": f"evt_{task_id}_3",
            "event_type": "eval_finished",
            "node": "run_eval",
            "message": "rule evaluation completed",
            "payload": {"overall_score": 0.92},
            "created_at": "2026-06-18T10:00:02+00:00",
        },
    ]
    state["events"] = recovered_events.copy()
    create_task(task_id, state["file_id"], state["question"], state)
    backfill_task_events(task_id, recovered_events[-1:])

    hydrate_state_events(state)

    assert [event["event_type"] for event in state["events"]] == [
        "task_created",
        "fields_matched",
        "eval_finished",
    ]
    events = list_analysis_events(task_id)
    assert [event["event_id"] for event in events] == [event["event_id"] for event in recovered_events]


def test_tool_events_include_summary_fields():
    state = _build_state(f"task_event_tool_{uuid.uuid4().hex[:8]}")
    create_task(state["task_id"], state["file_id"], state["question"], state)

    record_tool_called(
        state["task_id"],
        "groupby_aggregate",
        {
            "group_by": "region",
            "metric_column": "sales_amount",
            "aggregation": "sum",
            "sort_order": "desc",
            "limit": 5,
        },
    )
    record_tool_succeeded(
        state["task_id"],
        "groupby_aggregate",
        {
            "success": True,
            "tool_name": "groupby_aggregate",
            "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
            "summary": "East leads region sales.",
            "error": None,
            "metadata": {"elapsed_ms": 12},
            "metric_label": "sales_amount_sum",
        },
    )

    events = list_analysis_events(state["task_id"])
    tool_called = next(event for event in events if event["event_type"] == "tool_called")
    tool_succeeded = next(event for event in events if event["event_type"] == "tool_succeeded")

    assert "node_input_summary" in tool_called["payload"]
    assert "node_output_summary" in tool_called["payload"]
    assert "tool_result_summary" in tool_called["payload"]
    assert "node_input_summary" in tool_succeeded["payload"]
    assert "node_output_summary" in tool_succeeded["payload"]
    assert "tool_result_summary" in tool_succeeded["payload"]
