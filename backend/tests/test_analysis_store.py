import json
import uuid

from unittest.mock import patch

from app.storage.analysis_store import create_task, get_task_state, get_tool_call_logs, list_task_events, record_event


def test_analysis_task_roundtrip():
    state = {
        "task_id": "task_test",
        "file_id": "file_001",
        "question": "analyse category sales top 5",
        "analysis_goal": "compare category sales",
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

    create_task("task_test", "file_001", "analyse category sales top 5", state)
    record_event("task_test", "task_created", "create_task", "task created", {"status": "created"})

    loaded = get_task_state("task_test")
    events = list_task_events("task_test")

    assert loaded is not None
    assert loaded["task_id"] == "task_test"
    assert loaded["status"] == "created"
    assert events[0]["event_type"] == "task_created"


def test_get_tool_call_logs_returns_persisted_rows():
    from app.storage.analysis_store import record_tool_call
    task_id = f"task_tool_log_{uuid.uuid4().hex[:8]}"

    state = {
        "task_id": task_id,
        "file_id": "file_001",
        "question": "analyse category sales top 5",
        "analysis_goal": "compare category sales",
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

    create_task(task_id, "file_001", "analyse category sales top 5", state)
    record_tool_call(
        task_id,
        "groupby_aggregate",
        {"group_by": "product_category", "metric_column": "sales_amount"},
        {
            "success": True,
            "tool_name": "groupby_aggregate",
            "data": {"rows": [{"product_category": "electronics", "sales_amount_sum": 1200}]},
            "summary": "ok",
            "error": None,
            "metadata": {"elapsed_ms": 12},
        },
    )

    logs = get_tool_call_logs(task_id)

    assert len(logs) == 1
    assert logs[0]["tool_name"] == "groupby_aggregate"
    assert logs[0]["success"] is True
    assert json.loads(logs[0]["request_json"])["group_by"] == "product_category"


def test_analysis_store_preserves_insert_order_when_timestamps_match():
    from app.storage.analysis_store import record_tool_call

    task_id = f"task_store_order_{uuid.uuid4().hex[:8]}"
    state = {
        "task_id": task_id,
        "file_id": "file_001",
        "question": "analyse category sales top 5",
        "analysis_goal": "compare category sales",
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
    create_task(task_id, "file_001", "analyse category sales top 5", state)

    with patch("app.storage.analysis_store._ts", return_value="2026-06-18T10:00:00+00:00"):
        record_event(task_id, "task_created", "create_task", "task created", {"seq": 1})
        record_event(task_id, "dataset_profiled", "create_task", "dataset profiled", {"seq": 2})
        record_tool_call(
            task_id,
            "match_fields",
            {"seq": 1},
            {"success": True, "metadata": {"elapsed_ms": 1}},
        )
        record_tool_call(
            task_id,
            "groupby_aggregate",
            {"seq": 2},
            {"success": True, "metadata": {"elapsed_ms": 2}},
        )

    events = list_task_events(task_id)
    logs = get_tool_call_logs(task_id)

    assert [event["event_type"] for event in events] == ["task_created", "dataset_profiled"]
    assert [event["payload"]["seq"] for event in events] == [1, 2]
    assert [log["tool_name"] for log in logs] == ["match_fields", "groupby_aggregate"]
    assert [json.loads(log["request_json"])["seq"] for log in logs] == [1, 2]
