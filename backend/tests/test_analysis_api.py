import json

from fastapi.testclient import TestClient

from app.main import app
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord


def test_start_analysis_creates_task(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("product_category,sales_amount\nelectronics,1200\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_api",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=1,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                ]
            ),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    response = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api", "question": "analyse category sales top 5"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert response.json()["analysis_goal"] != ""
    assert len(response.json()["analysis_plan"]) > 0


def test_run_analysis_returns_completed_state(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_api_run",
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
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    start = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_run", "question": "analyse sales by region"},
    )
    task_id = start.json()["task_id"]

    run = client.post(f"/api/analysis/{task_id}/run")
    status = client.get(f"/api/analysis/{task_id}")
    events = client.get(f"/api/analysis/{task_id}/events")

    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert status.json()["task_id"] == task_id
    assert len(events.json()["events"]) > 0
