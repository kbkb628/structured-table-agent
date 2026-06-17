import json
import os
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.llm.qwen_client import QwenResponseError
from app.main import app
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.storage.session_store import SessionStore


class FakeRedisClient:
    def __init__(self):
        self.values: dict[str, str] = {}

    def get(self, key: str):
        return self.values.get(key)

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def delete(self, key: str):
        return 1 if self.values.pop(key, None) is not None else 0

    def eval(self, script: str, numkeys: int, key: str, token: str):
        del script, numkeys
        if self.values.get(key) == token:
            self.values.pop(key, None)
            return 1
        return 0

    def ping(self):
        return True


class FailingGoalLLMClient:
    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        del question
        del file_profile
        del business_context
        raise QwenResponseError("simulated provider failure")

    def generate_analysis_plan(self, analysis_goal: str, file_profile: dict, business_context: list[dict]) -> list[str]:
        del analysis_goal
        del file_profile
        del business_context
        return []

    def generate_report(
        self,
        analysis_goal: str,
        intermediate_findings: list[dict],
        chart_specs: list[dict],
        business_context: list[dict],
    ) -> dict:
        del analysis_goal
        del intermediate_findings
        del chart_specs
        del business_context
        return {}

    def judge_report(self, question: str, final_report: dict, tool_results: list[dict]) -> dict:
        del question
        del final_report
        del tool_results
        return {}


def _clear_provider_keys(monkeypatch):
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    for name in list(os.environ):
        if name.startswith("OPENAI_API_KEY"):
            monkeypatch.delenv(name, raising=False)


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
    assert "business_context" not in response.json()

    task_id = response.json()["task_id"]
    client = TestClient(app)
    state = client.get(f"/api/analysis/{task_id}")
    events = client.get(f"/api/analysis/{task_id}/events")

    assert len(state.json()["business_context"]) > 0
    assert "context_checkpoint" in state.json()
    assert state.json()["context_checkpoint"]["analysis_goal"] != ""
    assert any(event["event_type"] == "rag_retrieved" for event in events.json()["events"])


def test_start_analysis_returns_503_when_qwen_provider_is_misconfigured(tmp_path, monkeypatch):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("product_category,sales_amount\nelectronics,1200\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_api_llm_missing_key",
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
    monkeypatch.setenv("LLM_PROVIDER", "qwen")
    _clear_provider_keys(monkeypatch)

    client = TestClient(app)
    response = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_llm_missing_key", "question": "analyse category sales top 5"},
    )

    assert response.status_code == 503
    assert "API key" in response.json()["detail"]


def test_start_analysis_returns_502_when_provider_call_fails(tmp_path, monkeypatch):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("product_category,sales_amount\nelectronics,1200\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_api_llm_provider_error",
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
    monkeypatch.setattr("app.services.task_builder.get_llm_client", lambda: FailingGoalLLMClient())

    client = TestClient(app)
    response = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_llm_provider_error", "question": "analyse category sales top 5"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "simulated provider failure"


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
    assert "context_checkpoint" in status.json()
    assert "tool_call_logs" in status.json()
    assert len(status.json()["tool_call_logs"]) == 4
    assert len(events.json()["events"]) > 0


def test_run_channel_analysis_returns_multiple_tool_results(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "channel,sales_amount,order_id\nOnline,1200,ORD1\nRetail,800,ORD2\nOnline,300,ORD3\n",
        encoding="utf-8",
    )
    save_file_record(
        FileRecord(
            file_id="file_api_channel",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=3,
            columns_json=json.dumps(
                [
                    {"name": "channel", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
                    {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
                ]
            ),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    start = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_channel", "question": "analyse channel order count and sales performance"},
    )
    task_id = start.json()["task_id"]

    run = client.post(f"/api/analysis/{task_id}/run")

    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert len(run.json()["tool_results"]) == 2
    assert len(run.json()["chart_specs"]) == 2
    assert run.json()["pending_tool_calls"] == []
    assert run.json()["pending_metrics"] == []


def test_run_share_analysis_returns_share_rows(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "electronics,1200\n"
        "office,800\n"
        "electronics,1000\n",
        encoding="utf-8",
    )
    save_file_record(
        FileRecord(
            file_id="file_api_share",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
                ]
            ),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    start = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_share", "question": "analyse category sales share"},
    )
    task_id = start.json()["task_id"]

    run = client.post(f"/api/analysis/{task_id}/run")

    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["tool_results"][0]["tool_name"] == "calculate_share"
    assert "share_percent" in run.json()["tool_results"][0]["data"]["rows"][0]


def test_run_trend_analysis_returns_line_chart(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "order_date,sales_amount,order_id\n"
        "2026-06-03,800,ORD3\n"
        "2026-06-01,1200,ORD1\n"
        "2026-06-02,500,ORD2\n"
        "2026-06-01,300,ORD4\n",
        encoding="utf-8",
    )
    save_file_record(
        FileRecord(
            file_id="file_api_trend",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=4,
            column_count=3,
            columns_json=json.dumps(
                [
                    {"name": "order_date", "type": "date", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 4},
                    {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 4},
                ]
            ),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    start = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_trend", "question": "analyse sales trend by order date"},
    )
    task_id = start.json()["task_id"]

    run = client.post(f"/api/analysis/{task_id}/run")

    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["tool_results"][0]["tool_name"] == "trend_analysis"
    assert run.json()["chart_specs"][0]["chart_type"] == "line"


def test_run_anomaly_analysis_returns_anomaly_rows(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "beauty,10000\n"
        "apparel,1000\n"
        "electronics,1000\n"
        "office,1000\n"
        "home,1000\n"
        "food,1000\n",
        encoding="utf-8",
    )
    save_file_record(
        FileRecord(
            file_id="file_api_anomaly",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=6,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 6},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                ]
            ),
            created_at="2026-06-09T00:00:00+00:00",
        )
    )

    client = TestClient(app)
    start = client.post(
        "/api/analysis/start",
        json={"file_id": "file_api_anomaly", "question": "analyse category sales anomalies"},
    )
    task_id = start.json()["task_id"]

    run = client.post(f"/api/analysis/{task_id}/run")

    assert run.status_code == 200
    assert run.json()["status"] == "completed"
    assert run.json()["tool_results"][0]["tool_name"] == "anomaly_analysis"
    assert run.json()["tool_results"][0]["data"]["rows"][0]["is_anomaly"] is True


def test_eval_run_persists_eval_result(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n",
        encoding="utf-8",
    )
    save_file_record(
        FileRecord(
            file_id="file_api_eval",
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
        json={"file_id": "file_api_eval", "question": "analyse sales by region"},
    )
    task_id = start.json()["task_id"]
    client.post(f"/api/analysis/{task_id}/run")

    eval_response = client.post("/api/eval/run", json={"task_id": task_id})
    status = client.get(f"/api/analysis/{task_id}")

    assert eval_response.status_code == 200
    assert eval_response.json()["task_id"] == task_id
    assert eval_response.json()["eval_result"]["overall_score"] > 0
    assert status.json()["eval_result"]["overall_score"] == eval_response.json()["eval_result"]["overall_score"]


def test_eval_run_returns_404_for_missing_task():
    client = TestClient(app)

    response = client.post("/api/eval/run", json={"task_id": "task_missing"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def test_eval_cases_run_returns_fixed_case_summary():
    client = TestClient(app)

    response = client.post("/api/eval/cases/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_cases"] == 6
    assert payload["passed_cases"] == 6
    assert payload["failed_cases"] == 0
    assert payload["pass_rate"] == 1.0
    assert payload["average_tool_success_rate"] == 1.0
    assert payload["average_trace_completeness"] == 1.0
    assert payload["average_report_completeness"] == 1.0
    assert payload["average_chart_validity"] == 1.0
    assert payload["average_field_validity"] == 1.0
    assert len(payload["results"]) == 6


def test_get_analysis_tool_logs_returns_persisted_logs(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_api_logs",
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
        json={"file_id": "file_api_logs", "question": "analyse sales by region"},
    )
    task_id = start.json()["task_id"]
    client.post(f"/api/analysis/{task_id}/run")

    response = client.get(f"/api/analysis/{task_id}/tool-logs")

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_id"] == task_id
    assert len(payload["tool_call_logs"]) == 4
    assert payload["tool_call_logs"][0]["tool_name"] == "match_fields"
    assert payload["tool_call_logs"][-1]["tool_name"] == "generate_report"


def test_run_analysis_returns_409_when_task_is_already_locked(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    file_id = f"file_api_locked_{uuid.uuid4().hex[:8]}"
    save_file_record(
        FileRecord(
            file_id=file_id,
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
        json={"file_id": file_id, "question": "analyse sales by region"},
    )
    task_id = start.json()["task_id"]

    store = SessionStore()
    token = store.acquire_task_lock(task_id)

    try:
        run = client.post(f"/api/analysis/{task_id}/run")
    finally:
        if token is not None:
            store.release_task_lock(task_id, token)

    assert run.status_code == 409
    assert run.json()["detail"] == f"Task {task_id} is already running."


def test_get_analysis_falls_back_to_sqlite_when_redis_is_available_but_task_key_is_missing(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    file_id = f"file_api_redis_miss_{uuid.uuid4().hex[:8]}"
    save_file_record(
        FileRecord(
            file_id=file_id,
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
        json={"file_id": file_id, "question": "analyse sales by region"},
    )
    task_id = start.json()["task_id"]

    fake_client = FakeRedisClient()
    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        response = client.get(f"/api/analysis/{task_id}")

    assert response.status_code == 200
    assert response.json()["task_id"] == task_id
    assert response.json()["business_context"]
