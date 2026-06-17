import json
import uuid

from app.services.task_builder import build_file_profile_from_record
from app.services.task_builder import create_analysis_task
from app.storage.analysis_store import get_task_state, list_task_events
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord


class StubLLMClient:
    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        del question
        del file_profile
        del business_context
        return "qwen goal"

    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
    ) -> list[str]:
        del analysis_goal
        del file_profile
        del business_context
        return ["qwen plan step"]

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


def test_build_file_profile_from_record_returns_profile_dict(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount\nEast,1200\n", encoding="utf-8")
    save_file_record(
        FileRecord(
            file_id="file_builder_profile",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=1,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                ]
            ),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    profile = build_file_profile_from_record("file_builder_profile")

    assert profile is not None
    assert profile["file_id"] == "file_builder_profile"
    assert profile["columns"][0]["name"] == "region"


def test_create_analysis_task_persists_state_and_startup_events(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\n", encoding="utf-8")
    file_profile = {
        "file_id": "file_builder_task",
        "filename": "sales_orders.csv",
        "row_count": 1,
        "column_count": 3,
        "columns": [
            {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_builder_task",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=1,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    task_id, state = create_analysis_task(
        file_id="file_builder_task",
        question="analyse sales by region",
        source_node="test_builder",
        file_profile=file_profile,
        task_id=f"task_builder_case_{uuid.uuid4().hex[:8]}",
    )

    stored = get_task_state(task_id)
    events = list_task_events(task_id)

    assert task_id.startswith("task_builder_case_")
    assert state["analysis_goal"] != ""
    assert len(state["analysis_plan"]) > 0
    assert len(state["business_context"]) > 0
    assert stored is not None
    assert stored["question"] == "analyse sales by region"
    event_types = [event["event_type"] for event in events]
    assert "context_checkpoint_refreshed" in event_types
    assert [event_type for event_type in event_types if event_type != "context_checkpoint_refreshed"] == [
        "task_created",
        "dataset_profiled",
        "rag_retrieved",
        "goal_understood",
        "plan_generated",
    ]


def test_create_analysis_task_uses_configured_llm_client(tmp_path, monkeypatch):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text("region,sales_amount,order_id\nEast,1200,ORD1\n", encoding="utf-8")
    file_profile = {
        "file_id": "file_builder_task_stub",
        "filename": "sales_orders.csv",
        "row_count": 1,
        "column_count": 3,
        "columns": [
            {"name": "region", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_builder_task_stub",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=1,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    monkeypatch.setattr("app.services.task_builder.get_llm_client", lambda: StubLLMClient())

    task_id, state = create_analysis_task(
        file_id="file_builder_task_stub",
        question="analyse sales by region",
        source_node="test_builder",
        file_profile=file_profile,
        task_id=f"task_builder_stub_{uuid.uuid4().hex[:8]}",
    )

    stored = get_task_state(task_id)

    assert state["analysis_goal"] == "qwen goal"
    assert state["analysis_plan"] == ["qwen plan step"]
    assert stored is not None
    assert stored["analysis_goal"] == "qwen goal"
    assert stored["analysis_plan"] == ["qwen plan step"]
