import json
import uuid
from pathlib import Path

from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import create_task, get_task_state, get_tool_call_logs
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord


def test_run_analysis_task_updates_state_and_events(tmp_path: Path):
    task_id = f"task_runner_{uuid.uuid4().hex[:8]}"
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_task",
        "filename": "sales_orders.csv",
        "row_count": 2,
        "column_count": 3,
        "columns": [
            {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
        ],
        "created_at": "2026-06-09T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_task",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    create_task(
        task_id,
        "file_task",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_task",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [],
            "analysis_plan": ["match fields", "aggregate", "chart", "report"],
            "current_step": "created",
            "completed_steps": [],
            "intermediate_findings": [],
            "tool_results": [],
            "chart_specs": [],
            "draft_report": {},
            "final_report": {},
            "eval_result": {},
            "events": [],
            "errors": [],
            "status": "created",
        },
    )

    result = run_analysis_task(task_id)
    stored = get_task_state(task_id)

    assert result["status"] == "completed"
    assert stored["status"] == "completed"
    assert stored["field_understanding"]["dimension_field"] == "region"
    assert stored["tool_results"][0]["tool_name"] == "groupby_aggregate"
    assert stored["chart_specs"][0]["chart_type"] == "bar"
    assert stored["final_report"]["analysis_goal"] == "compare region sales"
    assert any(event["event_type"] == "task_completed" for event in stored["events"])
    assert len(get_tool_call_logs(task_id)) == 1


def test_run_analysis_task_supports_channel_dual_metrics(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "channel,sales_amount,order_id\nOnline,1200,ORD1\nRetail,800,ORD2\nOnline,300,ORD3\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_channel",
        "filename": "sales_orders.csv",
        "row_count": 3,
        "column_count": 3,
        "columns": [
            {"name": "channel", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
        ],
        "created_at": "2026-06-09T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_channel",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    create_task(
        "task_channel",
        "file_channel",
        "analyse channel order count and sales performance",
        {
            "task_id": "task_channel",
            "file_id": "file_channel",
            "question": "analyse channel order count and sales performance",
            "analysis_goal": "compare channel order and sales performance",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [],
            "analysis_plan": ["match fields", "aggregate orders", "aggregate sales", "chart", "report"],
            "current_step": "created",
            "completed_steps": [],
            "intermediate_findings": [],
            "tool_results": [],
            "chart_specs": [],
            "draft_report": {},
            "final_report": {},
            "eval_result": {},
            "events": [],
            "errors": [],
            "status": "created",
        },
    )

    result = run_analysis_task("task_channel")

    assert result["status"] == "completed"
    assert len(result["tool_results"]) == 2
    assert len(result["chart_specs"]) == 2
    assert len(result["intermediate_findings"]) == 2
    assert result["tool_results"][0]["data"]["rows"][0]["channel"] == "Online"
    assert any(item["metric_label"] == "order_count" for item in result["intermediate_findings"])
    assert any(item["metric_label"] == "sales_amount_sum" for item in result["intermediate_findings"])


def test_run_analysis_task_records_match_failure(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "channel,order_id\nOnline,ORD1\nRetail,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_bad_match",
        "filename": "sales_orders.csv",
        "row_count": 2,
        "column_count": 2,
        "columns": [
            {"name": "channel", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
        ],
        "created_at": "2026-06-09T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_bad_match",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=2,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    create_task(
        "task_bad_match",
        "file_bad_match",
        "analyse sales by region",
        {
            "task_id": "task_bad_match",
            "file_id": "file_bad_match",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [],
            "analysis_plan": ["match fields", "aggregate", "chart", "report"],
            "current_step": "created",
            "completed_steps": [],
            "intermediate_findings": [],
            "tool_results": [],
            "chart_specs": [],
            "draft_report": {},
            "final_report": {},
            "eval_result": {},
            "events": [],
            "errors": [],
            "status": "created",
        },
    )

    result = run_analysis_task("task_bad_match")

    assert result["status"] == "failed"
    assert result["current_step"] == "failed"
    assert result["errors"][0]["code"] == "MATCH_FIELDS_INCOMPLETE"
    assert any(event["event_type"] == "task_failed" for event in result["events"])
