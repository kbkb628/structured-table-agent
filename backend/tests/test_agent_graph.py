import json
from pathlib import Path

from app.agent.graph import build_analysis_graph, run_analysis_graph
from app.schemas.tool_schema import ToolResponse
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
    assert result["draft_report"]["draft_status"] == "ready_for_final_report"
    assert result["draft_report"]["analysis_goal"] == "compare region sales"
    assert result["final_report"]["analysis_goal"] == "compare region sales"
    assert result["eval_result"]["overall_score"] > 0


def test_run_analysis_graph_routes_to_next_metric_before_finishing(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "channel,sales_amount,order_id\nOnline,1200,ORD1\nRetail,800,ORD2\nOnline,300,ORD3\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_graph_channel",
        "filename": "sales_orders.csv",
        "row_count": 3,
        "column_count": 3,
        "columns": [
            {"name": "channel", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
            {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
            {"name": "order_id", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
        ],
        "created_at": "2026-06-17T00:00:00+00:00",
    }

    save_file_record(
        FileRecord(
            file_id="file_graph_channel",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        "task_graph_channel",
        "file_graph_channel",
        "analyse channel order count and sales performance",
        {
            "task_id": "task_graph_channel",
            "file_id": "file_graph_channel",
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

    result = run_analysis_graph("task_graph_channel")

    assert result["status"] == "completed"
    assert result["draft_report"]["metric_labels"] == ["order_count", "sales_amount_sum"]
    assert len(result["tool_results"]) == 2
    assert any(step == "route_next_step:continue" for step in result["completed_steps"])
    assert any(step == "route_next_step:finish" for step in result["completed_steps"])


def test_analysis_graph_includes_explicit_tool_result_validation_node():
    graph = build_analysis_graph()
    assert "validate_tool_result" in graph.builder.nodes
    assert graph.builder.branches["execute_tools"]["route_on_task_status"].ends["continue"] == "validate_tool_result"
    assert graph.builder.branches["validate_tool_result"]["route_on_task_status"].ends["continue"] == "route_next_step"


def test_run_analysis_graph_fails_on_empty_tool_rows_during_validation(tmp_path: Path, monkeypatch):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "region,sales_amount,order_id\nEast,1200,ORD1\nWest,800,ORD2\n",
        encoding="utf-8",
    )
    file_profile = {
        "file_id": "file_graph_empty",
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
            file_id="file_graph_empty",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=3,
            columns_json=json.dumps(file_profile["columns"]),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    create_task(
        "task_graph_empty",
        "file_graph_empty",
        "analyse sales by region",
        {
            "task_id": "task_graph_empty",
            "file_id": "file_graph_empty",
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

    def fake_invoke_tool(tool_name: str, **kwargs):
        if tool_name == "groupby_aggregate":
            return ToolResponse(
                success=True,
                tool_name=tool_name,
                summary="No rows returned.",
                data={"rows": []},
                error=None,
                metadata={},
            )
        from app.tools.registry import invoke_tool as real_invoke_tool
        return real_invoke_tool(tool_name, **kwargs)

    monkeypatch.setattr("app.agent.nodes.invoke_tool", fake_invoke_tool)

    result = run_analysis_graph("task_graph_empty")

    assert result["status"] == "failed"
    assert result["current_step"] == "failed"
    assert result["errors"][0]["code"] == "EMPTY_RESULT"
    assert "validate_tool_result" in result["completed_steps"]


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
