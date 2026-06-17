import json
import uuid

from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import create_task
from app.storage.analysis_store import get_task_state
from app.storage.analysis_store import list_task_events
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


def test_session_store_save_state_updates_sqlite_when_redis_is_unavailable():
    task_id = f"task_session_save_{uuid.uuid4().hex[:8]}"
    create_task(
        task_id,
        "file_session_save",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_session_save",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": {},
            "field_understanding": {},
            "business_context": [],
            "analysis_plan": ["match fields"],
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
    saved_with_redis = store.save_state(
        task_id,
        {
            "task_id": task_id,
            "file_id": "file_session_save",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": {},
            "field_understanding": {},
            "business_context": [],
            "analysis_plan": ["match fields"],
            "current_step": "completed",
            "completed_steps": ["match fields"],
            "intermediate_findings": [],
            "tool_results": [],
            "chart_specs": [],
            "draft_report": {},
            "final_report": {},
            "eval_result": {},
            "events": [],
            "errors": [],
            "status": "completed",
        },
    )
    stored = get_task_state(task_id)

    assert saved_with_redis is False
    assert stored is not None
    assert stored["status"] == "completed"
    assert stored["current_step"] == "completed"


def test_session_store_falls_back_to_sqlite_when_redis_is_available_but_task_key_is_missing():
    task_id = f"task_session_redis_miss_{uuid.uuid4().hex[:8]}"
    create_task(
        task_id,
        "file_session_redis_miss",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_session_redis_miss",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": {},
            "field_understanding": {},
            "business_context": [{"id": "metric_sales_amount", "title": "Sales Amount"}],
            "analysis_plan": ["match fields"],
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

    fake_client = FakeRedisClient()
    store = SessionStore()

    from unittest.mock import patch

    with patch.object(SessionStore, "_connect", lambda self: fake_client):
        loaded_state, used_redis = store.load_state(task_id)

    assert used_redis is False
    assert loaded_state is not None
    assert loaded_state["task_id"] == task_id
    assert loaded_state["business_context"][0]["title"] == "Sales Amount"


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


def test_session_store_persists_granular_redis_keys(monkeypatch):
    task_id = f"task_session_granular_{uuid.uuid4().hex[:8]}"
    create_task(
        task_id,
        "file_session_granular",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_session_granular",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": {},
            "field_understanding": {"dimension_field": "region"},
            "business_context": [{"id": "metric_sales_amount", "title": "Sales Amount"}],
            "analysis_plan": ["match fields", "aggregate"],
            "current_step": "report",
            "completed_steps": ["match fields"],
            "intermediate_findings": [{"summary": "East leads."}],
            "tool_results": [],
            "chart_specs": [],
            "draft_report": {"title": "Draft report"},
            "final_report": {},
            "eval_result": {},
            "events": [],
            "errors": [],
            "status": "running",
        },
    )

    fake_client = FakeRedisClient()
    monkeypatch.setattr(SessionStore, "_connect", lambda self: fake_client)

    store = SessionStore()
    saved_with_redis = store.save_state(task_id, get_task_state(task_id))

    assert saved_with_redis is True
    assert f"analysis_state:{task_id}" in fake_client.values
    assert f"draft_report:{task_id}" in fake_client.values
    assert f"intermediate_findings:{task_id}" in fake_client.values
    assert f"business_context:{task_id}" in fake_client.values
    assert f"latest_context:{task_id}" in fake_client.values
    stored_business_context = json.loads(fake_client.values[f"business_context:{task_id}"])
    assert stored_business_context[0]["title"] == "Sales Amount"
    latest_context = json.loads(fake_client.values[f"latest_context:{task_id}"])
    assert latest_context["analysis_goal"] == "compare region sales"
    assert latest_context["current_step"] == "report"
    assert latest_context["draft_report_status"] == "available"
    assert latest_context["business_context_titles"] == ["Sales Amount"]
    assert latest_context["finding_count"] == 1
    assert "business_context" not in latest_context


def test_session_store_load_state_hydrates_context_checkpoint_from_redis(monkeypatch):
    task_id = f"task_session_checkpoint_{uuid.uuid4().hex[:8]}"
    fake_client = FakeRedisClient()
    fake_client.values[f"analysis_state:{task_id}"] = json.dumps(
        {
            "task_id": task_id,
            "file_id": "file_session_checkpoint",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": {},
            "field_understanding": {},
            "business_context": [{"id": "metric_sales_amount", "title": "Sales Amount"}],
            "analysis_plan": ["match fields", "aggregate"],
            "current_step": "report",
            "completed_steps": ["match fields"],
            "intermediate_findings": [],
            "tool_results": [],
            "chart_specs": [],
            "draft_report": {},
            "final_report": {},
            "eval_result": {},
            "events": [],
            "errors": [],
            "status": "running",
        },
        ensure_ascii=False,
    )
    fake_client.values[f"draft_report:{task_id}"] = json.dumps({"title": "Draft report"}, ensure_ascii=False)
    fake_client.values[f"intermediate_findings:{task_id}"] = json.dumps(
        [{"summary": "East leads."}],
        ensure_ascii=False,
    )
    fake_client.values[f"business_context:{task_id}"] = json.dumps(
        [{"id": "metric_sales_amount", "title": "Sales Amount"}],
        ensure_ascii=False,
    )
    fake_client.values[f"latest_context:{task_id}"] = json.dumps(
        {
            "analysis_goal": "compare region sales",
            "current_step": "report",
            "draft_report_status": "available",
            "finding_count": 1,
        },
        ensure_ascii=False,
    )
    monkeypatch.setattr(SessionStore, "_connect", lambda self: fake_client)

    state, used_redis = SessionStore().load_state(task_id)

    assert used_redis is True
    assert state is not None
    assert state["draft_report"]["title"] == "Draft report"
    assert state["intermediate_findings"][0]["summary"] == "East leads."
    assert state["business_context"][0]["title"] == "Sales Amount"
    assert state["context_checkpoint"]["draft_report_status"] == "available"


def test_session_store_task_lock_blocks_duplicate_acquire():
    store = SessionStore()
    task_id = f"task_session_lock_{uuid.uuid4().hex[:8]}"

    first_token = store.acquire_task_lock(task_id)
    second_token = store.acquire_task_lock(task_id)

    assert first_token is not None
    assert second_token is None
    assert store.release_task_lock(task_id, first_token) is True
    assert store.acquire_task_lock(task_id) is not None


def test_session_store_task_lock_roundtrip_with_fake_redis(monkeypatch):
    fake_client = FakeRedisClient()
    monkeypatch.setattr(SessionStore, "_connect", lambda self: fake_client)
    store = SessionStore()
    task_id = f"task_session_lock_redis_{uuid.uuid4().hex[:8]}"

    token = store.acquire_task_lock(task_id)

    assert token is not None
    assert f"task_lock:{task_id}" in fake_client.values
    assert store.acquire_task_lock(task_id) is None
    assert store.release_task_lock(task_id, token) is True
    assert f"task_lock:{task_id}" not in fake_client.values
