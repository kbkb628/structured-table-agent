from fastapi.testclient import TestClient

from app.main import app


def test_sandbox_status_endpoint_reports_runtime_capabilities(monkeypatch):
    monkeypatch.setattr(
        "app.api.sandbox.describe_sandbox_runtime",
        lambda: {
            "enabled": True,
            "docker_available": True,
            "image": "python:3.12-slim",
            "network_disabled": True,
            "timeout_seconds": 8,
        },
    )

    client = TestClient(app)
    response = client.get("/api/sandbox/status")

    assert response.status_code == 200
    assert response.json()["enabled"] is True
    assert response.json()["docker_available"] is True


def test_sandbox_execute_endpoint_returns_execution_result(monkeypatch):
    monkeypatch.setattr(
        "app.api.sandbox.execute_in_docker_sandbox",
        lambda file_id, python_code, timeout_seconds=None: {
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"summary": "ok"}',
            "stderr": "",
            "elapsed_ms": 48,
            "parsed_output": {"summary": "ok"},
            "degraded": False,
        },
    )

    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "python_code": "print('ok')", "timeout_seconds": 8},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["parsed_output"]["summary"] == "ok"
