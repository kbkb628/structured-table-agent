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


def test_record_sandbox_execution_surfaces_execution_summary_fields():
    record_sandbox_execution(
        file_id="file_sandbox_template",
        request_payload={
            "python_code": "print('templated')",
            "template_name": "region_sales_summary",
            "timeout_seconds": 8,
        },
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

    assert latest["execution_mode"] == "template"
    assert latest["template_name"] == "region_sales_summary"
    assert latest["python_code_char_count"] == len("print('templated')")


def test_record_sandbox_execution_surfaces_template_result_summary():
    record_sandbox_execution(
        file_id="file_sandbox_template",
        request_payload={
            "python_code": "print('templated')",
            "template_name": "region_sales_summary",
            "timeout_seconds": 8,
        },
        response_payload={
            "status": "completed",
            "exit_code": 0,
            "stdout": '{"template_name":"region_sales_summary","top_region":"East","top_sales_amount":1200.0,"region_count":4}',
            "stderr": "",
            "elapsed_ms": 33,
            "parsed_output": {
                "template_name": "region_sales_summary",
                "top_region": "East",
                "top_sales_amount": 1200.0,
                "region_count": 4,
            },
            "degraded": False,
            "error": None,
        },
        execution_source="sandbox_api",
    )

    latest = get_latest_sandbox_execution()

    assert latest["parsed_output_keys"] == [
        "region_count",
        "template_name",
        "top_region",
        "top_sales_amount",
    ]
    assert latest["template_result_field_count"] == 3
    assert latest["template_result_summary"]["top_region"] == "East"
