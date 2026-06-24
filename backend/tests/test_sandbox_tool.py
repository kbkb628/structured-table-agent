from app.tools.registry import invoke_tool


def test_advanced_code_execution_tool_returns_structured_tool_response(monkeypatch):
    monkeypatch.setattr(
        "app.tools.sandbox_tool.execute_in_docker_sandbox",
        lambda file_id, python_code, timeout_seconds=None: {
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"rows": [{"region": "East", "sales_amount": 1200}]}',
            "stderr": "",
            "elapsed_ms": 55,
            "parsed_output": {"rows": [{"region": "East", "sales_amount": 1200}]},
            "degraded": False,
        },
    )

    result = invoke_tool(
        "advanced_code_execution",
        file_id="file_sandbox",
        python_code="print('hello')",
        timeout_seconds=8,
    )

    assert result.success is True
    assert result.tool_name == "advanced_code_execution"
    assert result.data["status"] == "completed"
    assert result.data["parsed_output"]["rows"][0]["region"] == "East"
