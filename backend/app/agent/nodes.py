from app.agent.state import AnalysisGraphState
from app.eval.rule_scorer import score_task_state
from app.storage.analysis_store import (
    list_task_events,
    record_eval_result,
    record_event,
    record_tool_call,
    update_task_state,
)
from app.tools.chart_tool import generate_chart
from app.tools.duckdb_tools import groupby_aggregate
from app.tools.match_fields import match_fields
from app.tools.report_tool import generate_report


def fail_task(state: AnalysisGraphState, code: str, message: str, payload: dict | None = None) -> AnalysisGraphState:
    error = {"code": code, "message": message, "details": payload or {}}
    state["errors"].append(error)
    state["status"] = "failed"
    state["current_step"] = "failed"
    record_event(state["task_id"], "task_failed", "langgraph", message, error)
    state["events"] = list_task_events(state["task_id"])
    update_task_state(state["task_id"], state)
    return state


def load_task_node(state: AnalysisGraphState) -> AnalysisGraphState:
    state["status"] = "running"
    state["current_step"] = "match_fields"
    update_task_state(state["task_id"], state)
    return state


def match_fields_node(state: AnalysisGraphState) -> AnalysisGraphState:
    field_result = match_fields(state["question"], state["file_profile"])
    state["field_understanding"] = field_result
    record_event(state["task_id"], "fields_matched", "match_fields", "matched analysis fields", field_result)
    metrics = field_result.get("metrics", [])

    if field_result.get("dimension_field") is None or not metrics:
        return fail_task(
            state,
            "MATCH_FIELDS_INCOMPLETE",
            "Failed to derive an executable field-matching plan.",
            {
                "candidate_fields": field_result.get("candidate_fields", []),
                "warnings": field_result.get("warnings", []),
            },
        )
    return state


def execute_tools_node(state: AnalysisGraphState) -> AnalysisGraphState:
    metrics = state["field_understanding"]["metrics"]
    dimension_field = state["field_understanding"]["dimension_field"]

    for metric in metrics:
        tool_request = {
            "file_id": state["file_id"],
            "group_by": dimension_field,
            "metric_column": metric["metric_field"],
            "aggregation": metric["aggregation"],
            "sort_order": "desc",
            "limit": 5,
        }
        record_event(state["task_id"], "tool_called", "groupby_aggregate", "calling groupby_aggregate", tool_request)
        tool_response = groupby_aggregate(**tool_request)
        tool_response_dict = tool_response.model_dump()
        tool_response_dict["metric_label"] = metric["label"]
        record_tool_call(state["task_id"], "groupby_aggregate", tool_request, tool_response_dict)

        if not tool_response.success:
            state["tool_results"].append(tool_response_dict)
            record_event(state["task_id"], "tool_failed", "groupby_aggregate", "groupby_aggregate failed", tool_response_dict)
            return fail_task(
                state,
                tool_response_dict["error"]["code"],
                tool_response_dict["error"]["message"],
                {"metric_label": metric["label"]},
            )

        rows = tool_response.data["rows"]
        if not rows:
            return fail_task(
                state,
                "EMPTY_RESULT",
                "The aggregation returned no rows.",
                {"metric_label": metric["label"]},
            )

        state["tool_results"].append(tool_response_dict)
        state["completed_steps"].append(f"groupby_aggregate:{metric['label']}")
        state["intermediate_findings"].append(
            {
                "metric_label": metric["label"],
                "summary": tool_response.summary,
                "top_row": rows[0],
            }
        )
        record_event(state["task_id"], "tool_succeeded", "groupby_aggregate", "groupby_aggregate succeeded", tool_response_dict)
    return state


def generate_charts_node(state: AnalysisGraphState) -> AnalysisGraphState:
    dimension_field = state["field_understanding"]["dimension_field"]

    for tool_result in state["tool_results"]:
        rows = tool_result.get("data", {}).get("rows", [])
        metric_label = tool_result.get("metric_label")
        y_field = next(key for key in rows[0].keys() if key != dimension_field)
        try:
            chart_spec = generate_chart(
                title=f"{dimension_field} vs {y_field}",
                x_field=dimension_field,
                y_field=y_field,
                rows=rows,
            )
            chart_spec["metric_label"] = metric_label
            state["chart_specs"].append(chart_spec)
            state["completed_steps"].append(f"generate_chart:{metric_label}")
            record_event(state["task_id"], "chart_generated", "generate_chart", "generated bar chart", chart_spec)
        except ValueError as exc:
            chart_error = {
                "code": "CHART_GENERATION_FAILED",
                "message": str(exc),
                "details": {"metric_label": metric_label},
            }
            state["errors"].append(chart_error)
            record_event(state["task_id"], "chart_failed", "generate_chart", "chart generation degraded", chart_error)
    return state


def generate_report_node(state: AnalysisGraphState) -> AnalysisGraphState:
    report = generate_report(
        question=state["question"],
        analysis_goal=state["analysis_goal"],
        tool_results=state["tool_results"],
        chart_specs=state["chart_specs"],
    )
    state["final_report"] = report
    state["completed_steps"].append("generate_report")
    record_event(state["task_id"], "report_generated", "generate_report", "generated final report", report)
    return state


def evaluate_report_node(state: AnalysisGraphState) -> AnalysisGraphState:
    state["current_step"] = "completed"
    state["status"] = "completed"
    record_event(state["task_id"], "task_completed", "langgraph", "analysis task completed", {"status": "completed"})
    state["events"] = list_task_events(state["task_id"])
    state["eval_result"] = score_task_state(state)
    record_eval_result(state["task_id"], state["eval_result"])
    record_event(state["task_id"], "eval_finished", "langgraph", "rule evaluation completed", state["eval_result"])
    state["events"] = list_task_events(state["task_id"])
    update_task_state(state["task_id"], state)
    return state
