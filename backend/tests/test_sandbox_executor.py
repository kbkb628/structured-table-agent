from app.sandbox.executor import DockerSandboxExecutor


def test_docker_sandbox_executor_reports_success(monkeypatch, tmp_path):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)

    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 0,
            "stdout": '{"result": {"top_region": "East"}}',
            "stderr": "",
            "elapsed_ms": 41,
        },
    )

    result = executor.execute_python(
        code="print('ignored')",
        mounted_files=[
            {
                "host_path": str(tmp_path / "sales.csv"),
                "container_path": "/workspace/input/sales.csv",
                "read_only": True,
            }
        ],
        timeout_seconds=8,
    )

    assert result["status"] == "completed"
    assert result["exit_code"] == 0
    assert result["parsed_output"]["result"]["top_region"] == "East"


def test_docker_sandbox_executor_reports_timeout(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)

    def raise_timeout(command, timeout_seconds):
        raise TimeoutError(f"timed out after {timeout_seconds}s")

    monkeypatch.setattr(executor, "_run_process", raise_timeout)

    result = executor.execute_python(code="while True: pass", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "timeout"
    assert result["degraded"] is True
    assert result["error"]["code"] == "SANDBOX_TIMEOUT"


def test_docker_sandbox_executor_reports_docker_unavailable(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: False)

    result = executor.execute_python(code="print(1)", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "degraded"
    assert result["error"]["code"] == "DOCKER_UNAVAILABLE"


def test_docker_sandbox_executor_classifies_syntax_error(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)
    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 1,
            "stdout": "",
            "stderr": "SyntaxError: invalid syntax",
            "elapsed_ms": 21,
        },
    )

    result = executor.execute_python(code="if True print('x')", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "failed"
    assert result["error"]["code"] == "SANDBOX_SYNTAX_ERROR"


def test_docker_sandbox_executor_classifies_network_error(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)
    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 1,
            "stdout": "",
            "stderr": "requests.exceptions.ConnectionError: [Errno -2] Name or service not known",
            "elapsed_ms": 18,
        },
    )

    result = executor.execute_python(code="import requests", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "failed"
    assert result["error"]["code"] == "SANDBOX_NETWORK_ERROR"


def test_docker_sandbox_executor_classifies_resource_killed_container(monkeypatch):
    executor = DockerSandboxExecutor()
    monkeypatch.setattr(executor, "docker_available", lambda: True)
    monkeypatch.setattr(
        executor,
        "_run_process",
        lambda command, timeout_seconds: {
            "returncode": 137,
            "stdout": "",
            "stderr": "Killed",
            "elapsed_ms": 25,
        },
    )

    result = executor.execute_python(code="x = '1' * 10_000_000", mounted_files=[], timeout_seconds=3)

    assert result["status"] == "failed"
    assert result["error"]["code"] == "SANDBOX_RESOURCE_KILLED"
