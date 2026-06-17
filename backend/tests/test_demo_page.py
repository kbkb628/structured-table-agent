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
    assert 'id="question-input"' in content
    assert 'id="run-analysis-button"' in content
    assert 'id="task-status"' in content
    assert 'id="task-summary"' in content
    assert 'id="chart-preview"' in content
    assert 'id="chart-empty-state"' in content
    assert 'id="report-list"' in content
    assert 'id="report-output"' in content
    assert 'id="events-output"' in content
    assert 'id="tool-logs-output"' in content


def test_root_path_remains_unregistered():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 404
