import json
import uuid

from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import create_task
from app.storage.analysis_store import list_task_events
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.storage.session_store import SessionStore


def test_session_store_falls_back_to_sqlite_when_redis_unavailable(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_session_store",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(
                [
                    {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                ]
            ),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    task_id = f"task_session_store_{uuid.uuid4().hex[:8]}"
    create_task(
        task_id,
        "file_session_store",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_session_store",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": {
                "file_id": "file_session_store",
                "filename": "sales_orders.csv",
                "row_count": 2,
                "column_count": 3,
                "columns": [
                    {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                ],
                "created_at": "2026-06-17T00:00:00+00:00",
            },
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

    store = SessionStore()
    loaded_state, used_redis = store.load_state(task_id)

    assert used_redis is False
    assert loaded_state is not None
    assert loaded_state["task_id"] == task_id


def test_run_analysis_task_records_session_store_warning_when_redis_is_unavailable(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    file_profile = {
        "file_id": "file_session_warning",
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
            file_id="file_session_warning",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    task_id = f"task_session_warning_{uuid.uuid4().hex[:8]}"
    create_task(
        task_id,
        "file_session_warning",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_session_warning",
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
    events = list_task_events(task_id)

    assert result["status"] == "completed"
    assert any(event["event_type"] == "session_store_warning" for event in events)
