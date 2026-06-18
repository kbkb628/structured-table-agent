from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.storage.analysis_store import create_task
from app.storage.analysis_store import record_tool_call
from app.storage.analysis_store import update_task_state
from app.storage.analysis_store import record_event
from app.storage.analysis_store import backfill_task_events
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

    with patch(
        "app.storage.analysis_store._ts",
        side_effect=["2099-12-31T23:59:58+00:00", "2099-12-31T23:59:59+00:00"],
    ):
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
        "tool_results": [
            {
                "success": True,
                "tool_name": "groupby_aggregate",
                "metadata": {"elapsed_ms": 12, "retry_attempts": 1, "retry_status": "recovered"},
            },
            {
                "success": False,
                "tool_name": "generate_chart",
                "metadata": {"elapsed_ms": 7, "retry_attempts": 2, "retry_status": "exhausted"},
            },
        ],
        "chart_specs": [{"chart_type": "bar"}],
        "draft_report": {"title": "Draft report"},
        "final_report": {
            "title": "Final report",
            "analysis_goal": "compare region sales",
            "key_findings": [
                {
                    "finding": "East leads.",
                    "evidence": "sales_amount_sum=1200",
                    "source_tool": "groupby_aggregate",
                }
            ],
            "chart_explanations": ["Bar chart compares region sales."],
            "business_suggestions": ["Check channel mix in East."],
            "data_limitations": ["Uploaded CSV only."],
            "next_steps": ["Drill down by channel."],
        },
        "llm_judgement": {"supported_by_tools": True, "has_findings": True, "issue_count": 0},
        "eval_result": {
            "overall_score": 0.91,
            "schema_valid": True,
            "tool_success_rate": 1.0,
            "field_validity": True,
            "chart_validity": True,
            "report_completeness": 1.0,
            "trace_completeness": 1.0,
            "issues": [],
        },
        "pending_metrics": [{"label": "sales_amount_sum"}],
        "pending_tool_calls": [{"tool_name": "groupby_aggregate", "label": "sales_amount_sum"}],
        "context_checkpoint": {
            "analysis_goal": "compare region sales",
            "current_step": "report",
            "draft_report_status": "available",
            "latest_error_code": "CHART_DEGRADED",
        },
        "tool_call_logs": [{"tool_name": "groupby_aggregate"}],
        "events": [
            {
                "event_id": "evt_project_status_latest_artifacts_1",
                "event_type": "task_created",
                "node": "start_analysis",
                "message": "task created",
                "payload": {"status": "created"},
                "created_at": "2099-12-31T23:59:51+00:00",
            },
            {
                "event_id": "evt_project_status_latest_artifacts_2",
                "event_type": "report_generated",
                "node": "generate_report",
                "message": "report generated",
                "payload": {"title": "Final report"},
                "created_at": "2099-12-31T23:59:58+00:00",
            },
        ],
        "errors": [
            {
                "code": "CHART_DEGRADED",
                "message": "chart generation degraded to empty preview",
            }
        ],
        "status": "completed",
    }
    with patch("app.storage.analysis_store._ts", return_value="2099-12-31T23:59:59+00:00"):
        create_task(task_id, state["file_id"], state["question"], state)
        update_task_state(task_id, state)
    backfill_task_events(task_id, state["events"])
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
    assert latest_task["evaluation"]["has_eval_result"] is True
    assert latest_task["evaluation"]["overall_score"] == 0.91
    assert latest_task["evaluation"]["issue_count"] == 0
    assert latest_task["evaluation"]["has_dimension_scores"] is True
    assert latest_task["judgement"]["supported_by_tools"] is True
    assert latest_task["judgement"]["has_findings"] is True
    assert latest_task["judgement"]["issue_count"] == 0
    assert latest_task["process"]["pending_metric_count"] == 1
    assert latest_task["process"]["planned_tool_call_count"] == 1
    assert latest_task["process"]["event_count"] >= 2
    assert latest_task["process"]["latest_event_type"] == "report_generated"
    assert latest_task["process"]["llm_issue_count"] == 0
    assert latest_task["report"]["chart_spec_count"] == 1
    assert latest_task["report"]["key_finding_count"] == 1
    assert latest_task["report"]["business_suggestion_count"] == 1
    assert latest_task["report"]["data_limitation_count"] == 1
    assert latest_task["report"]["next_step_count"] == 1
    assert latest_task["context"]["business_context_count"] == 1
    assert latest_task["context"]["top_business_context_title"] == "Sales Amount"
    assert latest_task["context"]["checkpoint_current_step"] == "report"
    assert latest_task["context"]["checkpoint_draft_report_status"] == "available"
    assert latest_task["context"]["checkpoint_latest_error_code"] == "CHART_DEGRADED"
    assert latest_task["semantics"]["analysis_goal"] == "compare region sales"
    assert latest_task["semantics"]["analysis_plan_count"] == 3
    assert latest_task["semantics"]["current_step"] == "report"
    assert latest_task["semantics"]["completed_step_count"] == 2
    assert latest_task["semantics"]["finding_count"] == 1
    assert latest_task["semantics"]["dimension_field"] == "region"
    assert latest_task["semantics"]["metric_count"] == 1
    assert latest_task["tools"]["tool_result_count"] == 2
    assert latest_task["tools"]["successful_tool_result_count"] == 1
    assert latest_task["tools"]["failed_tool_result_count"] == 1
    assert latest_task["tools"]["total_tool_elapsed_ms"] == 19
    assert latest_task["tools"]["latest_tool_name"] == "groupby_aggregate"
    assert latest_task["tools"]["retried_tool_result_count"] == 2
    assert latest_task["tools"]["retry_attempts_total"] == 3
    assert latest_task["tools"]["latest_retry_status"] == "exhausted"
    assert latest_task["errors"]["error_count"] == 1
    assert latest_task["errors"]["latest_error_code"] == "CHART_DEGRADED"
    assert latest_task["errors"]["latest_error_message"] == "chart generation degraded to empty preview"
    assert latest_task["errors"]["has_degradation"] is True
