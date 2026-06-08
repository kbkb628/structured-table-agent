from app.storage.analysis_store import (
    get_task_state,
    list_task_events,
    record_event,
    record_tool_call,
    update_task_state,
)
from app.tools.chart_tool import generate_chart
from app.tools.duckdb_tools import groupby_aggregate
from app.tools.match_fields import match_fields
from app.tools.report_tool import generate_report


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

    tool_request = {
        "file_id": state["file_id"],
        "group_by": field_result["dimension_field"],
        "metric_column": field_result["metric_field"],
        "aggregation": field_result["aggregation"],
        "sort_order": "desc",
        "limit": 5,
    }
    record_event(task_id, "tool_called", "groupby_aggregate", "calling groupby_aggregate", tool_request)
    tool_response = groupby_aggregate(**tool_request)
    tool_response_dict = tool_response.model_dump()
    record_tool_call(task_id, "groupby_aggregate", tool_request, tool_response_dict)

    if not tool_response.success:
        state["tool_results"].append(tool_response_dict)
        state["errors"].append(tool_response_dict)
        state["status"] = "failed"
        record_event(task_id, "tool_failed", "groupby_aggregate", "groupby_aggregate failed", tool_response_dict)
        state["events"] = list_task_events(task_id)
        update_task_state(task_id, state)
        return state

    state["tool_results"].append(tool_response_dict)
    state["completed_steps"].append("groupby_aggregate")
    record_event(task_id, "tool_succeeded", "groupby_aggregate", "groupby_aggregate succeeded", tool_response_dict)

    rows = tool_response.data["rows"]
    y_field = next(key for key in rows[0].keys() if key != field_result["dimension_field"])
    chart_spec = generate_chart(
        title=f"{field_result['dimension_field']} vs {y_field}",
        x_field=field_result["dimension_field"],
        y_field=y_field,
        rows=rows,
    )
    state["chart_specs"].append(chart_spec)
    state["completed_steps"].append("generate_chart")
    record_event(task_id, "chart_generated", "generate_chart", "generated bar chart", chart_spec)

    report = generate_report(
        question=state["question"],
        analysis_goal=state["analysis_goal"],
        tool_result=tool_response_dict,
        chart_spec=chart_spec,
    )
    state["final_report"] = report
    state["completed_steps"].append("generate_report")
    state["current_step"] = "completed"
    state["status"] = "completed"
    record_event(task_id, "report_generated", "generate_report", "generated final report", report)
    record_event(task_id, "task_completed", "run_analysis_task", "analysis task completed", {"status": "completed"})

    state["events"] = list_task_events(task_id)
    update_task_state(task_id, state)
    return state
