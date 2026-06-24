from app.sandbox.store import get_latest_sandbox_execution
from app.sandbox.store import record_sandbox_execution


def test_record_sandbox_execution_round_trips_latest_execution():
    record_sandbox_execution(
        file_id="file_sandbox",
        request_payload={"python_code": "print('ok')"},
        response_payload={
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"summary": "ok"}',
            "stderr": "",
            "elapsed_ms": 33,
            "parsed_output": {"summary": "ok"},
            "degraded": False,
            "error": None,
        },
        execution_source="sandbox_api",
    )

    latest = get_latest_sandbox_execution()

    assert latest["file_id"] == "file_sandbox"
    assert latest["execution_source"] == "sandbox_api"
    assert latest["status"] == "completed"
    assert latest["parsed_output"]["summary"] == "ok"
