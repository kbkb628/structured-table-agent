import json
import os
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.llm.qwen_client import QwenResponseError
from app.main import app
from app.storage.analysis_store import create_task, get_task_state, list_task_events, record_event
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
    monkeypatch.delenv("TONGYI_API_KEY", raising=False)
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
    assert run.json()["chart_specs"][0]["plotly_spec"]["layout"]["yaxis"]["title"] == "share_percent"
    assert run.json()["chart_specs"][0]["plotly_spec"]["data"][0]["y"] == [73.33, 26.67]


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


def test_eval_run_uses_session_store_state_when_redis_snapshot_is_newer():
    task_id = f"task_eval_redis_state_{uuid.uuid4().hex[:8]}"
    stale_state = {
        "task_id": task_id,
        "file_id": "file_eval_redis_state",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": ["match fields", "aggregate", "chart", "report"],
        "current_step": "completed",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "llm_judgement": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "completed",
    }
    create_task(task_id, "file_eval_redis_state", "analyse sales by region", stale_state)
    for event_type in [
        "task_created",
        "fields_matched",
        "tool_succeeded",
        "chart_generated",
        "report_generated",
        "task_completed",
    ]:
        record_event(task_id, event_type, "test_eval", event_type, {})

    richer_state = {
        **stale_state,
        "field_understanding": {"dimension_field": "region", "metric_field": "sales_amount"},
        "tool_results": [
            {
                "success": True,
                "tool_name": "groupby_aggregate",
                "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
                "summary": "East leads region sales.",
                "error": None,
                "metadata": {"elapsed_ms": 12},
            }
        ],
        "chart_specs": [{"chart_type": "bar", "plotly_spec": {"data": [{"type": "bar"}]}}],
        "final_report": {
            "title": "Analysis Report: analyse sales by region",
            "analysis_goal": "compare region sales",
            "key_findings": [{"finding": "East performs best", "evidence": "1200", "source_tool": "groupby_aggregate"}],
            "chart_explanations": ["Bar chart generated for bar view."],
            "business_suggestions": ["Focus on East."],
            "data_limitations": ["Uploaded CSV only."],
            "next_steps": ["Check by channel."],
        },
    }

    fake_client = FakeRedisClient()
    fake_client.values[f"analysis_state:{task_id}"] = json.dumps(richer_state, ensure_ascii=False)

    client = TestClient(app)
    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        response = client.post("/api/eval/run", json={"task_id": task_id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["eval_result"]["report_completeness"] == 1.0
    assert payload["eval_result"]["field_validity"] is True
    assert payload["eval_result"]["tool_success_rate"] == 1.0


def test_eval_run_uses_redis_snapshot_even_when_sqlite_row_is_missing():
    task_id = f"task_eval_redis_only_{uuid.uuid4().hex[:8]}"
    redis_only_state = {
        "task_id": task_id,
        "file_id": "file_eval_redis_only",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {"dimension_field": "region", "metric_field": "sales_amount"},
        "business_context": [],
        "analysis_plan": ["match fields", "aggregate", "chart", "report"],
        "current_step": "completed",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [
            {
                "success": True,
                "tool_name": "groupby_aggregate",
                "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
                "summary": "East leads region sales.",
                "error": None,
                "metadata": {"elapsed_ms": 12},
            }
        ],
        "chart_specs": [{"chart_type": "bar", "plotly_spec": {"data": [{"type": "bar"}]}}],
        "draft_report": {},
        "final_report": {
            "title": "Analysis Report: analyse sales by region",
            "analysis_goal": "compare region sales",
            "key_findings": [{"finding": "East performs best", "evidence": "1200", "source_tool": "groupby_aggregate"}],
            "chart_explanations": ["Bar chart generated for bar view."],
            "business_suggestions": ["Focus on East."],
            "data_limitations": ["Uploaded CSV only."],
            "next_steps": ["Check by channel."],
        },
        "llm_judgement": {},
        "eval_result": {},
        "events": [
            {
                "event_id": f"evt_{task_id}_1",
                "event_type": "task_created",
                "node": "start_analysis",
                "message": "task created",
                "payload": {"status": "created"},
                "created_at": "2026-06-18T10:00:00+00:00",
            },
            {
                "event_id": f"evt_{task_id}_2",
                "event_type": "fields_matched",
                "node": "match_fields",
                "message": "matched analysis fields",
                "payload": {},
                "created_at": "2026-06-18T10:00:01+00:00",
            },
            {
                "event_id": f"evt_{task_id}_3",
                "event_type": "tool_succeeded",
                "node": "groupby_aggregate",
                "message": "groupby_aggregate succeeded",
                "payload": {},
                "created_at": "2026-06-18T10:00:02+00:00",
            },
            {
                "event_id": f"evt_{task_id}_4",
                "event_type": "chart_generated",
                "node": "generate_chart",
                "message": "generated bar chart",
                "payload": {},
                "created_at": "2026-06-18T10:00:03+00:00",
            },
            {
                "event_id": f"evt_{task_id}_5",
                "event_type": "report_generated",
                "node": "generate_report",
                "message": "generated final report",
                "payload": {},
                "created_at": "2026-06-18T10:00:04+00:00",
            },
            {
                "event_id": f"evt_{task_id}_6",
                "event_type": "task_completed",
                "node": "langgraph",
                "message": "analysis task completed",
                "payload": {"status": "completed"},
                "created_at": "2026-06-18T10:00:05+00:00",
            },
        ],
        "errors": [],
        "status": "completed",
    }

    fake_client = FakeRedisClient()
    fake_client.values[f"analysis_state:{task_id}"] = json.dumps(redis_only_state, ensure_ascii=False)

    client = TestClient(app)
    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        response = client.post("/api/eval/run", json={"task_id": task_id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_id"] == task_id
    assert payload["eval_result"]["overall_score"] > 0
    assert payload["eval_result"]["trace_completeness"] == 1.0
    stored = get_task_state(task_id)
    assert stored is not None
    assert stored["task_id"] == task_id
    persisted_events = list_task_events(task_id)
    assert persisted_events
    assert any(event["event_type"] == "task_created" for event in persisted_events)


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


def test_run_analysis_uses_redis_snapshot_even_when_sqlite_row_is_missing():
    task_id = f"task_run_redis_only_{uuid.uuid4().hex[:8]}"
    redis_only_state = {
        "task_id": task_id,
        "file_id": "file_run_redis_only",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": ["match fields", "aggregate"],
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "llm_judgement": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }

    fake_client = FakeRedisClient()
    fake_client.values[f"analysis_state:{task_id}"] = json.dumps(redis_only_state, ensure_ascii=False)

    client = TestClient(app)
    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        with patch("app.api.analysis.run_analysis_task", return_value={**redis_only_state, "status": "completed"}):
            response = client.post(f"/api/analysis/{task_id}/run")

    assert response.status_code == 200
    assert response.json()["task_id"] == task_id
    assert response.json()["status"] == "completed"
    stored = get_task_state(task_id)
    assert stored is not None
    assert stored["task_id"] == task_id


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


def test_get_analysis_uses_redis_snapshot_even_when_sqlite_row_is_missing():
    task_id = f"task_api_redis_only_{uuid.uuid4().hex[:8]}"
    redis_only_state = {
        "task_id": task_id,
        "file_id": "file_api_redis_only",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {"dimension_field": "region", "metric_field": "sales_amount"},
        "business_context": [{"id": "redis_metric", "title": "Redis Sales Amount"}],
        "analysis_plan": ["match fields", "aggregate"],
        "current_step": "report",
        "completed_steps": ["match fields"],
        "intermediate_findings": [{"summary": "Redis says East leads."}],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {"title": "Redis draft report"},
        "final_report": {"title": "Redis final report", "analysis_goal": "compare region sales"},
        "llm_judgement": {"supported_by_tools": True, "issue_count": 0},
        "eval_result": {},
        "events": [
            {
                "event_id": f"evt_{task_id}_1",
                "event_type": "task_created",
                "node": "start_analysis",
                "message": "task created",
                "payload": {"status": "created"},
                "created_at": "2026-06-18T10:00:00+00:00",
            }
        ],
        "errors": [],
        "status": "running",
        "context_checkpoint": {
            "analysis_goal": "compare region sales",
            "current_step": "report",
            "status": "running",
            "draft_report_status": "available",
            "finding_count": 1,
        },
    }

    fake_client = FakeRedisClient()
    fake_client.values[f"analysis_state:{task_id}"] = json.dumps(redis_only_state, ensure_ascii=False)

    client = TestClient(app)
    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        response = client.get(f"/api/analysis/{task_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task_id
    assert body["draft_report"]["title"] == "Redis draft report"
    assert body["final_report"]["title"] == "Redis final report"
    assert body["llm_judgement"]["supported_by_tools"] is True
    assert body["business_context"][0]["title"] == "Redis Sales Amount"
    assert body["events"][0]["event_type"] == "task_created"
    stored = get_task_state(task_id)
    assert stored is not None
    assert stored["task_id"] == task_id


def test_get_analysis_events_uses_redis_snapshot_when_sqlite_timeline_is_missing():
    task_id = f"task_events_redis_only_{uuid.uuid4().hex[:8]}"
    redis_only_state = {
        "task_id": task_id,
        "file_id": "file_events_redis_only",
        "question": "analyse sales by region",
        "analysis_goal": "compare region sales",
        "file_profile": {},
        "field_understanding": {},
        "business_context": [],
        "analysis_plan": ["match fields", "aggregate"],
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "llm_judgement": {},
        "eval_result": {},
        "events": [
            {
                "event_id": f"evt_{task_id}_1",
                "event_type": "task_created",
                "node": "start_analysis",
                "message": "task created",
                "payload": {"status": "created"},
                "created_at": "2026-06-18T10:00:00+00:00",
            }
        ],
        "errors": [],
        "status": "created",
    }

    fake_client = FakeRedisClient()
    fake_client.values[f"analysis_state:{task_id}"] = json.dumps(redis_only_state, ensure_ascii=False)

    client = TestClient(app)
    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        response = client.get(f"/api/analysis/{task_id}/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["task_id"] == task_id
    assert payload["events"][0]["event_type"] == "task_created"
    persisted_events = list_task_events(task_id)
    assert persisted_events
    assert any(event["event_type"] == "task_created" for event in persisted_events)


def test_get_analysis_uses_granular_redis_recovery_when_snapshot_is_missing(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n", encoding="utf-8")
    file_id = f"file_api_granular_recovery_{uuid.uuid4().hex[:8]}"
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
    fake_client.values[f"draft_report:{task_id}"] = json.dumps({"title": "Redis draft report"}, ensure_ascii=False)
    fake_client.values[f"final_report:{task_id}"] = json.dumps(
        {"title": "Redis final report", "analysis_goal": "compare region sales"},
        ensure_ascii=False,
    )
    fake_client.values[f"llm_judgement:{task_id}"] = json.dumps(
        {"supported_by_tools": True, "issue_count": 0},
        ensure_ascii=False,
    )
    fake_client.values[f"intermediate_findings:{task_id}"] = json.dumps(
        [{"summary": "Redis says East leads."}],
        ensure_ascii=False,
    )
    fake_client.values[f"business_context:{task_id}"] = json.dumps(
        [{"id": "redis_metric", "title": "Redis Sales Amount"}],
        ensure_ascii=False,
    )
    fake_client.values[f"latest_context:{task_id}"] = json.dumps(
        {
            "analysis_goal": "compare region sales",
            "current_step": "report",
            "status": "running",
            "draft_report_status": "available",
            "finding_count": 1,
        },
        ensure_ascii=False,
    )

    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        response = client.get(f"/api/analysis/{task_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == task_id
    assert body["draft_report"]["title"] == "Redis draft report"
    assert body["final_report"]["title"] == "Redis final report"
    assert body["llm_judgement"]["supported_by_tools"] is True
    assert body["intermediate_findings"][0]["summary"] == "Redis says East leads."
    assert body["business_context"][0]["title"] == "Redis Sales Amount"
    recovery_events = client.get(f"/api/analysis/{task_id}/events").json()["events"]
    recovery_types = [event["event_type"] for event in recovery_events]
    assert "session_state_recovered" in recovery_types
