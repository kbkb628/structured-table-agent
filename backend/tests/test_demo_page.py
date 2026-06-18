from fastapi.testclient import TestClient

from app.main import app


def test_demo_page_returns_html():
    client = TestClient(app)

    response = client.get("/demo")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_demo_page_contains_upload_and_analysis_sections():
    client = TestClient(app)

    response = client.get("/demo")
    content = response.text

    assert "Structured Table Analysis Demo" in content
    assert 'id="upload-form"' in content
    assert 'id="load-sample-button"' in content
    assert 'id="question-input"' in content
    assert 'id="run-analysis-button"' in content
    assert 'id="provider-status-button"' in content
    assert 'id="provider-smoke-button"' in content
    assert 'id="project-status-button"' in content
    assert 'id="eval-cases-button"' in content
    assert 'id="task-status"' in content
    assert 'id="task-summary"' in content
    assert 'id="provider-pill"' in content
    assert 'id="provider-meta"' in content
    assert 'id="provider-diag"' in content
    assert 'id="session-store-pill"' in content
    assert 'id="session-store-meta"' in content
    assert 'id="session-store-output"' in content
    assert 'warning_count' in content
    assert 'latest_warning_task_id' in content
    assert 'latest_recovered_task_id' in content
    assert 'latest_task_artifacts_output' in content
    assert 'has_business_context' in content
    assert 'has_llm_judgement' in content
    assert 'latest_task_eval_output' in content
    assert 'has_eval_result' in content
    assert 'overall_score' in content
    assert 'issue_count' in content
    assert 'latest_task_judgement_output' in content
    assert 'supported_by_tools' in content
    assert 'has_findings' in content
    assert 'latest_task_process_output' in content
    assert 'pending_metric_count' in content
    assert 'planned_tool_call_count' in content
    assert 'latest_event_type' in content
    assert 'latest_task_report_output' in content
    assert 'chart_spec_count' in content
    assert 'key_finding_count' in content
    assert 'business_suggestion_count' in content
    assert 'latest_task_context_output' in content
    assert 'business_context_count' in content
    assert 'top_business_context_title' in content
    assert 'checkpoint_current_step' in content
    assert 'latest_task_semantics_output' in content
    assert 'analysis_goal' in content
    assert 'analysis_plan_count' in content
    assert 'completed_step_count' in content
    assert 'dimension_field' in content
    assert 'latest_task_tools_output' in content
    assert 'tool_result_count' in content
    assert 'successful_tool_result_count' in content
    assert 'total_tool_elapsed_ms' in content
    assert 'retried_tool_result_count' in content
    assert 'retry_attempts_total' in content
    assert 'latest_retry_status' in content
    assert 'latest_task_errors_output' in content
    assert 'error_count' in content
    assert 'latest_error_code' in content
    assert 'has_degradation' in content
    assert 'id="project-status-summary"' in content
    assert 'id="project-status-output"' in content
    assert 'id="eval-summary"' in content
    assert 'id="eval-results-output"' in content
    assert 'id="chart-preview"' in content
    assert 'id="chart-empty-state"' in content
    assert 'id="report-list"' in content
    assert 'id="report-output"' in content
    assert 'id="events-output"' in content
    assert 'id="tool-logs-output"' in content
    assert "sales_orders.csv" in content
    assert "/api/llm/provider-status" in content
    assert "/api/llm/provider-smoke" in content
    assert "/api/project-status" in content
    assert "/api/eval/cases/run" in content
    assert "session store runtime mode" in content.lower()


def test_root_path_remains_unregistered():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 404
