from app.eval.rule_scorer import score_task_state
from app.storage.analysis_store import (
    get_task_state,
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


def _fail_task(state: dict, task_id: str, code: str, message: str, payload: dict | None = None) -> dict:
    error = {"code": code, "message": message, "details": payload or {}}
    state["errors"].append(error)
    state["status"] = "failed"
    state["current_step"] = "failed"
    record_event(task_id, "task_failed", "run_analysis_task", message, error)
    state["events"] = list_task_events(task_id)
    update_task_state(task_id, state)
    return state


def run_analysis_task(task_id: str) -> dict:
    state = get_task_state(task_id)
    if state is None:
        raise ValueError(f"Task {task_id} not found")

    state["status"] = "running"
    state["current_step"] = "match_fields"
    update_task_state(task_id, state)

    field_result = match_fields(state["question"], state["file_profile"])
    state["field_understanding"] = field_result
    record_event(task_id, "fields_matched", "match_fields", "matched analysis fields", field_result)
    metrics = field_result.get("metrics", [])

    if field_result.get("dimension_field") is None or not metrics:
        return _fail_task(
            state,
            task_id,
            "MATCH_FIELDS_INCOMPLETE",
            "Failed to derive an executable field-matching plan.",
            {
                "candidate_fields": field_result.get("candidate_fields", []),
                "warnings": field_result.get("warnings", []),
            },
        )

    for metric in metrics:
        tool_request = {
            "file_id": state["file_id"],
            "group_by": field_result["dimension_field"],
            "metric_column": metric["metric_field"],
            "aggregation": metric["aggregation"],
            "sort_order": "desc",
            "limit": 5,
        }
        record_event(task_id, "tool_called", "groupby_aggregate", "calling groupby_aggregate", tool_request)
        tool_response = groupby_aggregate(**tool_request)
        tool_response_dict = tool_response.model_dump()
        tool_response_dict["metric_label"] = metric["label"]
        record_tool_call(task_id, "groupby_aggregate", tool_request, tool_response_dict)

        if not tool_response.success:
            state["tool_results"].append(tool_response_dict)
            record_event(task_id, "tool_failed", "groupby_aggregate", "groupby_aggregate failed", tool_response_dict)
            return _fail_task(
                state,
                task_id,
                tool_response_dict["error"]["code"],
                tool_response_dict["error"]["message"],
                {"metric_label": metric["label"]},
            )

        rows = tool_response.data["rows"]
        if not rows:
            return _fail_task(
                state,
                task_id,
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
        record_event(task_id, "tool_succeeded", "groupby_aggregate", "groupby_aggregate succeeded", tool_response_dict)

        y_field = next(key for key in rows[0].keys() if key != field_result["dimension_field"])
        try:
            chart_spec = generate_chart(
                title=f"{field_result['dimension_field']} vs {y_field}",
                x_field=field_result["dimension_field"],
                y_field=y_field,
                rows=rows,
            )
            chart_spec["metric_label"] = metric["label"]
            state["chart_specs"].append(chart_spec)
            state["completed_steps"].append(f"generate_chart:{metric['label']}")
            record_event(task_id, "chart_generated", "generate_chart", "generated bar chart", chart_spec)
        except ValueError as exc:
            chart_error = {
                "code": "CHART_GENERATION_FAILED",
                "message": str(exc),
                "details": {"metric_label": metric["label"]},
            }
            state["errors"].append(chart_error)
            record_event(task_id, "chart_failed", "generate_chart", "chart generation degraded", chart_error)

    report = generate_report(
        question=state["question"],
        analysis_goal=state["analysis_goal"],
        tool_results=state["tool_results"],
        chart_specs=state["chart_specs"],
    )
    state["final_report"] = report
    state["completed_steps"].append("generate_report")
    state["current_step"] = "completed"
    state["status"] = "completed"
    record_event(task_id, "report_generated", "generate_report", "generated final report", report)
    record_event(task_id, "task_completed", "run_analysis_task", "analysis task completed", {"status": "completed"})
    state["events"] = list_task_events(task_id)
    state["eval_result"] = score_task_state(state)
    record_eval_result(task_id, state["eval_result"])
    record_event(task_id, "eval_finished", "run_analysis_task", "rule evaluation completed", state["eval_result"])
    state["events"] = list_task_events(task_id)
    update_task_state(task_id, state)
    return state
