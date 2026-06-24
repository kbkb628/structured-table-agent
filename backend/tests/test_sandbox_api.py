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


def test_sandbox_execute_endpoint_persists_latest_execution(monkeypatch):
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
            "error": None,
        },
    )
    captured = {}
    monkeypatch.setattr(
        "app.api.sandbox.record_sandbox_execution",
        lambda **kwargs: captured.update(kwargs),
    )

    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "python_code": "print('ok')", "timeout_seconds": 8},
    )

    assert response.status_code == 200
    assert captured["file_id"] == "file_sandbox"
    assert captured["execution_source"] == "sandbox_api"
    assert captured["response_payload"]["status"] == "completed"


def test_sandbox_execute_endpoint_accepts_template_name(monkeypatch):
    monkeypatch.setattr(
        "app.api.sandbox.execute_in_docker_sandbox",
        lambda file_id, python_code, timeout_seconds=None: {
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"summary": "ok"}',
            "stderr": "",
            "elapsed_ms": 40,
            "parsed_output": {"summary": "ok"},
            "degraded": False,
            "error": None,
        },
    )
    monkeypatch.setattr(
        "app.api.sandbox.build_sandbox_template_code",
        lambda template_name: "print('templated')",
    )

    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "template_name": "region_sales_summary", "timeout_seconds": 8},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_sandbox_execute_endpoint_rejects_excessive_timeout():
    client = TestClient(app)
    response = client.post(
        "/api/sandbox/execute",
        json={"file_id": "file_sandbox", "python_code": "print('ok')", "timeout_seconds": 999},
    )

    assert response.status_code == 422
