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
