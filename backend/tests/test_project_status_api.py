from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.storage.analysis_store import create_task
from app.storage.analysis_store import record_tool_call
from app.storage.analysis_store import update_task_state
from app.storage.analysis_store import record_event
from app.storage.session_store import SessionStore


def test_get_project_status_reports_current_counters(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    monkeypatch.setenv("OPENAI_API_KEY_0011AI", "test-key")

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["provider"]["provider"] == "qwen"
    assert payload["summary"]["provider"]["diagnostics"]["smoke_ready"] is True
    assert payload["summary"]["demo"]["available"] is True
    assert payload["summary"]["session_store"]["preferred_backend"] == "redis"
    assert payload["summary"]["database"]["tables"]
    assert "analysis_tasks" in payload["summary"]["database"]["tables"]
    assert "analysis_events" in payload["summary"]["database"]["tables"]


def test_get_project_status_includes_live_counts():
    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["database"]["tables"]["analysis_tasks"]["exists"] is True
    assert payload["summary"]["database"]["tables"]["analysis_events"]["exists"] is True
    assert payload["summary"]["database"]["tables"]["tool_call_logs"]["exists"] is True
    assert payload["summary"]["database"]["tables"]["eval_results"]["exists"] is True
    assert payload["summary"]["session_store"]["degraded_to_sqlite"] is True


def test_get_project_status_reports_redis_session_store_when_available(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://fake-redis:6379/0")
    client = TestClient(app)

    with patch.object(SessionStore, "_connect", lambda self: object()):
        response = client.get("/api/project-status")

    assert response.status_code == 200
    payload = response.json()
    session_store = payload["summary"]["session_store"]
    assert session_store["preferred_backend"] == "redis"
    assert session_store["active_backend"] == "redis"
    assert session_store["redis_available"] is True
    assert session_store["degraded_to_sqlite"] is False


def test_get_project_status_aggregates_session_store_event_summary():
    warning_task_id = "task_project_status_warning"
    recovered_task_id = "task_project_status_recovered"
    client = TestClient(app)

    baseline_response = client.get("/api/project-status")
    assert baseline_response.status_code == 200
    baseline_summary = baseline_response.json()["summary"]["session_store"]["event_summary"]

    record_event(
        warning_task_id,
        "session_store_warning",
        "session_store",
        "session store downgraded to SQLite",
        {"reason": "redis_unavailable"},
    )
    record_event(
        recovered_task_id,
        "session_state_recovered",
        "session_store",
        "session state recovered from granular Redis keys",
        {"recovery_source": "sqlite_plus_granular_redis"},
    )

    response = client.get("/api/project-status")

    assert response.status_code == 200
    event_summary = response.json()["summary"]["session_store"]["event_summary"]
    assert event_summary["warning_count"] >= baseline_summary["warning_count"] + 1
    assert event_summary["recovered_count"] >= baseline_summary["recovered_count"] + 1
    assert event_summary["latest_warning_task_id"] == warning_task_id
    assert event_summary["latest_recovered_task_id"] == recovered_task_id
    assert event_summary["latest_warning_at"]
    assert event_summary["latest_recovered_at"]


def test_get_project_status_reports_latest_task_artifact_coverage():
    task_id = "task_project_status_latest_artifacts"
    state = {
        "task_id": task_id,
        "file_id": "file_project_status_latest_artifacts",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {"dimension_field": "region"},
        "business_context": [{"id": "metric_sales_amount", "title": "Sales Amount"}],
        "analysis_plan": ["match fields", "aggregate", "report"],
        "current_step": "report",
        "completed_steps": ["match fields", "aggregate"],
        "intermediate_findings": [{"summary": "East leads."}],
        "tool_results": [{"success": True, "tool_name": "groupby_aggregate"}],
        "chart_specs": [{"chart_type": "bar"}],
        "draft_report": {"title": "Draft report"},
        "final_report": {"title": "Final report", "analysis_goal": "compare region sales"},
        "llm_judgement": {"supported_by_tools": True, "issue_count": 0},
        "eval_result": {"overall_score": 0.91},
        "context_checkpoint": {
            "analysis_goal": "compare region sales",
            "current_step": "report",
            "draft_report_status": "available",
        },
        "tool_call_logs": [{"tool_name": "groupby_aggregate"}],
        "events": [],
        "errors": [],
        "status": "completed",
    }
    with patch("app.storage.analysis_store._ts", return_value="2099-12-31T23:59:59+00:00"):
        create_task(task_id, state["file_id"], state["question"], state)
        update_task_state(task_id, state)
    record_tool_call(
        task_id,
        "groupby_aggregate",
        {"group_by": "region", "metric_column": "sales_amount"},
        {
            "success": True,
            "tool_name": "groupby_aggregate",
            "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
            "summary": "ok",
            "error": None,
            "metadata": {"elapsed_ms": 12},
        },
    )

    client = TestClient(app)
    response = client.get("/api/project-status")

    assert response.status_code == 200
    latest_task = response.json()["summary"]["latest_task"]
    assert latest_task["task_id"] == task_id
    assert latest_task["status"] == "completed"
    assert latest_task["artifacts"]["has_business_context"] is True
    assert latest_task["artifacts"]["has_context_checkpoint"] is True
    assert latest_task["artifacts"]["has_draft_report"] is True
    assert latest_task["artifacts"]["has_final_report"] is True
    assert latest_task["artifacts"]["has_llm_judgement"] is True
    assert latest_task["artifacts"]["tool_call_log_count"] >= 1
