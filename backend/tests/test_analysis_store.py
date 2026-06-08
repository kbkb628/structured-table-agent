from app.storage.analysis_store import create_task, get_task_state, list_task_events, record_event


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
