import json
import uuid
from pathlib import Path

from app.llm.qwen_client import QwenResponseError
from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import create_task, get_task_state, get_tool_call_logs
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord


class RunnerStubLLMClient:
    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        del question
        del file_profile
        del business_context
        return "runner stub goal"

    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
    ) -> list[str]:
        del analysis_goal
        del file_profile
        del business_context
        return ["runner stub plan"]

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
        return {
            "title": "LLM Final Report",
            "analysis_goal": "compare region sales",
            "key_findings": [
                {
                    "finding": "East performs best",
                    "evidence": "LLM grounded this in deterministic tool output.",
                    "source_tool": "groupby_aggregate",
                }
            ],
            "chart_explanations": ["Bar chart compares regional sales totals."],
            "business_suggestions": ["Expand the strongest region playbook."],
            "data_limitations": ["Limited to the uploaded sample data."],
            "next_steps": ["Investigate regional segment drivers."],
        }

    def judge_report(self, question: str, final_report: dict, tool_results: list[dict]) -> dict:
        del question
        del final_report
        del tool_results
        return {
            "supported_by_tools": True,
            "has_findings": True,
            "issue_count": 0,
            "issues": [],
        }


class FailingReportLLMClient:
    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        del question
        del file_profile
        del business_context
        return "failing report goal"

    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
    ) -> list[str]:
        del analysis_goal
        del file_profile
        del business_context
        return ["failing report plan"]

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
        raise QwenResponseError("simulated report failure")

    def judge_report(self, question: str, final_report: dict, tool_results: list[dict]) -> dict:
        del question
        del final_report
        del tool_results
        return {}


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
    assert stored["draft_report"]["draft_status"] == "ready_for_final_report"
    assert stored["final_report"]["analysis_goal"] == "compare region sales"
    assert any(event["event_type"] == "task_completed" for event in stored["events"])
    checkpoint_events = [event for event in stored["events"] if event["event_type"] == "context_checkpoint_refreshed"]
    assert checkpoint_events
    assert checkpoint_events[-1]["payload"]["analysis_goal"] == "compare region sales"
    assert checkpoint_events[-1]["payload"]["draft_report_status"] == "available"
    assert "business_context_titles" in checkpoint_events[-1]["payload"]
    assert "business_context" not in checkpoint_events[-1]["payload"]
    tool_events = [
        event for event in stored["events"]
        if event["event_type"] in {"tool_called", "tool_succeeded"} and event["node"] == "groupby_aggregate"
    ]
    assert tool_events
    assert any("node_input_summary" in event["payload"] for event in tool_events)
    assert any("node_output_summary" in event["payload"] for event in tool_events)
    assert any("tool_result_summary" in event["payload"] for event in tool_events)
    assert any(event["payload"]["tool_result_summary"]["retry_status"] in {"not_needed", "recovered"} for event in tool_events)
    tool_logs = get_tool_call_logs(task_id)
    assert len(tool_logs) == 4
    assert [item["tool_name"] for item in tool_logs] == [
        "match_fields",
        "groupby_aggregate",
        "generate_chart",
        "generate_report",
    ]


def test_run_analysis_task_uses_llm_final_report_and_records_judgement(tmp_path: Path, monkeypatch):
    task_id = f"task_runner_llm_{uuid.uuid4().hex[:8]}"
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_task_llm",
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
            file_id="file_task_llm",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        task_id,
        "file_task_llm",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_task_llm",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [{"title": "Region"}],
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

    monkeypatch.setattr("app.agent.nodes.get_llm_client", lambda: RunnerStubLLMClient())

    result = run_analysis_task(task_id)
    stored = get_task_state(task_id)

    assert result["final_report"]["title"] == "LLM Final Report"
    assert stored["final_report"]["title"] == "LLM Final Report"
    assert result["llm_judgement"]["supported_by_tools"] is True
    assert stored["llm_judgement"]["issue_count"] == 0


def test_run_analysis_task_supports_category_sales_share_question(tmp_path: Path):
    task_id = f"task_runner_share_{uuid.uuid4().hex[:8]}"
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "electronics,1200\n"
        "office,800\n"
        "electronics,1000\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_task_share",
        "filename": "sales_orders.csv",
        "row_count": 3,
        "column_count": 2,
        "columns": [
            {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_task_share",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=2,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        task_id,
        "file_task_share",
        "analyse category sales share",
        {
            "task_id": task_id,
            "file_id": "file_task_share",
            "question": "analyse category sales share",
            "analysis_goal": "compare category sales share",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [{"title": "Product Category"}],
            "analysis_plan": ["match fields", "share analysis", "chart", "report"],
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
        },
    )

    result = run_analysis_task(task_id)

    assert result["status"] == "completed"
    assert result["tool_results"][0]["tool_name"] == "calculate_share"
    assert result["tool_results"][0]["data"]["rows"][0]["product_category"] == "electronics"
    assert "share_ratio" in result["tool_results"][0]["data"]["rows"][0]
    assert result["chart_specs"][0]["chart_type"] == "bar"
    assert result["chart_specs"][0]["plotly_spec"]["layout"]["yaxis"]["title"] == "share_percent"
    assert result["chart_specs"][0]["plotly_spec"]["data"][0]["y"] == [73.33, 26.67]


def test_run_analysis_task_supports_sales_trend_question(tmp_path: Path):
    task_id = f"task_runner_trend_{uuid.uuid4().hex[:8]}"
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "order_date,sales_amount,order_id\n"
        "2026-06-03,800,ORD3\n"
        "2026-06-01,1200,ORD1\n"
        "2026-06-02,500,ORD2\n"
        "2026-06-01,300,ORD4\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_task_trend",
        "filename": "sales_orders.csv",
        "row_count": 4,
        "column_count": 3,
        "columns": [
            {"name": "order_date", "type": "date", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 4},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 4},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_task_trend",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=4,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        task_id,
        "file_task_trend",
        "analyse sales trend by order date",
        {
            "task_id": task_id,
            "file_id": "file_task_trend",
            "question": "analyse sales trend by order date",
            "analysis_goal": "analyse sales trend over time",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [{"title": "Time Trend"}],
            "analysis_plan": ["match fields", "trend analysis", "chart", "report"],
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
        },
    )

    result = run_analysis_task(task_id)

    assert result["status"] == "completed"
    assert result["tool_results"][0]["tool_name"] == "trend_analysis"
    assert [row["order_date"] for row in result["tool_results"][0]["data"]["rows"]] == [
        "2026-06-01",
        "2026-06-02",
        "2026-06-03",
    ]
    assert result["chart_specs"][0]["chart_type"] == "line"


def test_run_analysis_task_supports_category_sales_anomalies(tmp_path: Path):
    task_id = f"task_runner_anomaly_{uuid.uuid4().hex[:8]}"
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
    file_profile = {
        "file_id": "file_task_anomaly",
        "filename": "sales_orders.csv",
        "row_count": 6,
        "column_count": 2,
        "columns": [
            {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 6},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_task_anomaly",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=6,
            column_count=2,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        task_id,
        "file_task_anomaly",
        "analyse category sales anomalies",
        {
            "task_id": task_id,
            "file_id": "file_task_anomaly",
            "question": "analyse category sales anomalies",
            "analysis_goal": "detect abnormal category sales",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [{"title": "Category"}],
            "analysis_plan": ["match fields", "anomaly analysis", "chart", "report"],
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
        },
    )

    result = run_analysis_task(task_id)

    assert result["status"] == "completed"
    assert result["tool_results"][0]["tool_name"] == "anomaly_analysis"
    assert result["tool_results"][0]["data"]["rows"][0]["product_category"] == "beauty"
    assert result["tool_results"][0]["data"]["rows"][0]["is_anomaly"] is True
    assert result["chart_specs"][0]["chart_type"] == "bar"
    assert result["chart_specs"][0]["plotly_spec"]["layout"]["yaxis"]["title"] == "z_score"
    assert result["chart_specs"][0]["plotly_spec"]["data"][0]["y"] == [2.2361]


def test_run_analysis_task_completes_when_anomaly_analysis_finds_no_outliers(tmp_path: Path):
    task_id = f"task_runner_anomaly_none_{uuid.uuid4().hex[:8]}"
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "beauty,1000\n"
        "apparel,1100\n"
        "electronics,1050\n"
        "office,1020\n"
        "home,1080\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_task_anomaly_none",
        "filename": "sales_orders.csv",
        "row_count": 5,
        "column_count": 2,
        "columns": [
            {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 5},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 5},
        ],
        "created_at": "2026-06-18T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_task_anomaly_none",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=5,
            column_count=2,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-18T00:00:00+00:00",
        )
    )

    create_task(
        task_id,
        "file_task_anomaly_none",
        "analyse category sales anomalies",
        {
            "task_id": task_id,
            "file_id": "file_task_anomaly_none",
            "question": "analyse category sales anomalies",
            "analysis_goal": "detect abnormal category sales",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [{"title": "Category"}],
            "analysis_plan": ["match fields", "anomaly analysis", "chart", "report"],
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
        },
    )

    result = run_analysis_task(task_id)

    assert result["status"] == "completed"
    assert result["tool_results"][0]["tool_name"] == "anomaly_analysis"
    assert result["tool_results"][0]["data"]["rows"] == []
    assert result["chart_specs"] == []
    assert result["errors"] == []


def test_run_analysis_task_marks_failed_when_llm_report_generation_fails(tmp_path: Path, monkeypatch):
    task_id = f"task_runner_llm_fail_{uuid.uuid4().hex[:8]}"
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_task_llm_fail",
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
            file_id="file_task_llm_fail",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        task_id,
        "file_task_llm_fail",
        "analyse sales by region",
        {
            "task_id": task_id,
            "file_id": "file_task_llm_fail",
            "question": "analyse sales by region",
            "analysis_goal": "compare region sales",
            "file_profile": file_profile,
            "field_understanding": {},
            "business_context": [{"title": "Region"}],
            "analysis_plan": ["match fields", "aggregate", "chart", "report"],
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
        },
    )

    monkeypatch.setattr("app.agent.nodes.get_llm_client", lambda: FailingReportLLMClient())

    result = run_analysis_task(task_id)
    stored = get_task_state(task_id)

    assert result["status"] == "failed"
    assert stored["status"] == "failed"
    assert result["errors"][0]["code"] == "LLM_REPORT_FAILED"
    assert any(event["event_type"] == "task_failed" for event in stored["events"])


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
    assert result["draft_report"]["chart_labels"] == ["order_count", "sales_amount_sum"]
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
