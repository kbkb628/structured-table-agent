import json
from pathlib import Path

from app.agent.graph import run_analysis_graph
from app.storage.analysis_store import create_task
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord


def test_run_analysis_graph_completes_region_task(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_graph",
        "filename": "sales_orders.csv",
        "row_count": 2,
        "column_count": 3,
        "columns": [
            {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_graph",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        "task_graph",
        "file_graph",
        "analyse sales by region",
        {
            "task_id": "task_graph",
            "file_id": "file_graph",
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

    result = run_analysis_graph("task_graph")

    assert result["status"] == "completed"
    assert result["final_report"]["analysis_goal"] == "compare region sales"
    assert result["eval_result"]["overall_score"] > 0


def test_run_analysis_graph_returns_failed_state_for_bad_match(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "channel,order_id\nOnline,ORD1\nRetail,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_graph_bad",
        "filename": "sales_orders.csv",
        "row_count": 2,
        "column_count": 2,
        "columns": [
            {"name": "channel", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_graph_bad",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=2,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        "task_graph_bad",
        "file_graph_bad",
        "analyse sales by region",
        {
            "task_id": "task_graph_bad",
            "file_id": "file_graph_bad",
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

    result = run_analysis_graph("task_graph_bad")

    assert result["status"] == "failed"
    assert result["errors"][0]["code"] == "MATCH_FIELDS_INCOMPLETE"
