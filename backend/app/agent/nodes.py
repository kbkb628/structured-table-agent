from app.agent.state import AnalysisGraphState
from app.eval.rule_scorer import score_task_state
from app.llm.factory import get_llm_client
from app.observability.event_logger import hydrate_state_events
from app.observability.event_logger import record_chart_failed
from app.observability.event_logger import record_chart_generated
from app.observability.event_logger import record_eval_finished
from app.observability.event_logger import record_fields_matched
from app.observability.event_logger import record_report_generated
from app.observability.event_logger import record_task_completed
from app.observability.event_logger import record_task_failed
from app.observability.event_logger import record_tool_called
from app.observability.event_logger import record_tool_failed
from app.observability.event_logger import record_tool_succeeded
from app.schemas.report_schema import FinalReport
from app.storage.analysis_store import record_eval_result, record_tool_call
from app.storage.session_store import SessionStore
from app.tools.registry import invoke_tool
from app.tools.registry import invoke_tool_with_retry


def _persist_state(state: AnalysisGraphState) -> None:
    SessionStore().save_state(state["task_id"], state)


def fail_task(state: AnalysisGraphState, code: str, message: str, payload: dict | None = None) -> AnalysisGraphState:
    error = {"code": code, "message": message, "details": payload or {}}
    state["errors"].append(error)
    state["status"] = "failed"
    state["current_step"] = "failed"
    record_task_failed(state["task_id"], "langgraph", message, error)
    hydrate_state_events(state)
    _persist_state(state)
    return state


def load_task_node(state: AnalysisGraphState) -> AnalysisGraphState:
    state["status"] = "running"
    state["current_step"] = "match_fields"
    _persist_state(state)
    return state


def match_fields_node(state: AnalysisGraphState) -> AnalysisGraphState:
    tool_request = {"question": state["question"], "file_profile": state["file_profile"]}
    record_tool_called(state["task_id"], "match_fields", tool_request)
    field_response = invoke_tool("match_fields", **tool_request)
    record_tool_call(state["task_id"], "match_fields", tool_request, field_response.model_dump())
    field_result = field_response.data or {}
    state["field_understanding"] = field_result
    record_fields_matched(state["task_id"], field_result)
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
    state["pending_metrics"] = metrics.copy()
    state["pending_tool_calls"] = (field_result.get("planned_tool_calls") or []).copy()
    return state


def execute_tools_node(state: AnalysisGraphState) -> AnalysisGraphState:
    pending_tool_calls = state.get("pending_tool_calls") or state["field_understanding"].get("planned_tool_calls") or []
    metrics = state.get("pending_metrics") or state["field_understanding"]["metrics"]
    metric = metrics[0]
    planned_call = pending_tool_calls[0] if pending_tool_calls else {
        "tool_name": "groupby_aggregate",
        "group_by": state["field_understanding"]["dimension_field"],
        "metric_column": metric["metric_field"],
        "aggregation": metric["aggregation"],
        "sort_order": "desc",
        "limit": 5,
        "label": metric["label"],
    }
    tool_name = str(planned_call["tool_name"])
    tool_request = {
        "file_id": state["file_id"],
        "group_by": planned_call["group_by"],
        "metric_column": planned_call["metric_column"],
        "aggregation": planned_call["aggregation"],
        "sort_order": planned_call["sort_order"],
        "limit": planned_call["limit"],
    }
    record_tool_called(state["task_id"], tool_name, tool_request)
    tool_response = invoke_tool_with_retry(tool_name, **tool_request)
    tool_response_dict = tool_response.model_dump()
    tool_response_dict["metric_label"] = metric["label"]
    tool_response_dict["selected_tool"] = tool_name
    record_tool_call(state["task_id"], tool_name, tool_request, tool_response_dict)
    state["_latest_tool_result"] = tool_response_dict
    state["_latest_tool_request"] = tool_request
    state["_latest_metric"] = metric
    return state


def validate_tool_result_node(state: AnalysisGraphState) -> AnalysisGraphState:
    tool_result = state.get("_latest_tool_result") or {}
    metric = state.get("_latest_metric") or {}
    tool_name = str(tool_result.get("selected_tool") or tool_result.get("tool_name") or "unknown_tool")
    state["completed_steps"].append("validate_tool_result")

    if not tool_result.get("success"):
        state["tool_results"].append(tool_result)
        record_tool_failed(state["task_id"], tool_name, tool_result)
        error = tool_result.get("error") or {}
        return fail_task(
            state,
            str(error.get("code") or "TOOL_EXECUTION_FAILED"),
            str(error.get("message") or "Tool execution failed."),
            {"metric_label": metric.get("label")},
        )

    rows = (tool_result.get("data") or {}).get("rows") or []
    if not rows:
        state["tool_results"].append(tool_result)
        record_tool_failed(state["task_id"], tool_name, tool_result)
        return fail_task(
            state,
            "EMPTY_RESULT",
            "The aggregation returned no rows.",
            {"metric_label": metric.get("label")},
        )

    state["tool_results"].append(tool_result)
    state["completed_steps"].append(f"{tool_name}:{metric['label']}")
    state["intermediate_findings"].append(
        {
            "metric_label": metric["label"],
            "summary": tool_result.get("summary", ""),
            "top_row": rows[0],
        }
    )
    state["pending_metrics"] = (state.get("pending_metrics") or [])[1:]
    state["pending_tool_calls"] = (state.get("pending_tool_calls") or [])[1:]
    state.pop("_latest_tool_result", None)
    state.pop("_latest_tool_request", None)
    state.pop("_latest_metric", None)
    record_tool_succeeded(state["task_id"], tool_name, tool_result)
    return state


def route_next_step_node(state: AnalysisGraphState) -> AnalysisGraphState:
    pending_metrics = state.get("pending_metrics", [])
    pending_tool_calls = state.get("pending_tool_calls", [])
    if pending_metrics or pending_tool_calls:
        state["current_step"] = "execute_tools"
        state["completed_steps"].append("route_next_step:continue")
        state["next_step"] = "execute_tools"
    else:
        state["current_step"] = "generate_charts"
        state["completed_steps"].append("route_next_step:finish")
        state["next_step"] = "generate_charts"
    _persist_state(state)
    return state


def generate_charts_node(state: AnalysisGraphState) -> AnalysisGraphState:
    dimension_field = state["field_understanding"]["dimension_field"]

    for tool_result in state["tool_results"]:
        rows = tool_result.get("data", {}).get("rows", [])
        metric_label = tool_result.get("metric_label")
        y_field = next(key for key in rows[0].keys() if key != dimension_field)
        tool_request = {
            "title": f"{dimension_field} vs {y_field}",
            "x_field": dimension_field,
            "y_field": y_field,
            "rows": rows,
        }
        record_tool_called(state["task_id"], "generate_chart", tool_request)
        chart_response = invoke_tool_with_retry(
            "generate_chart",
            **tool_request,
        )
        chart_response_dict = chart_response.model_dump()
        chart_response_dict["metric_label"] = metric_label
        record_tool_call(state["task_id"], "generate_chart", tool_request, chart_response_dict)
        if chart_response.success:
            chart_spec = chart_response.data or {}
            chart_spec["metric_label"] = metric_label
            state["chart_specs"].append(chart_spec)
            state["completed_steps"].append(f"generate_chart:{metric_label}")
            record_chart_generated(state["task_id"], chart_spec)
        else:
            chart_error = {
                "code": "CHART_GENERATION_FAILED",
                "message": chart_response.error.message if chart_response.error else "Chart generation failed.",
                "details": {"metric_label": metric_label},
            }
            state["errors"].append(chart_error)
            record_chart_failed(state["task_id"], chart_error)
    return state


def _build_draft_report(state: AnalysisGraphState) -> dict:
    metric_labels = [item.get("metric_label", "unknown_metric") for item in state["intermediate_findings"]]
    chart_labels = [item.get("metric_label", "unknown_metric") for item in state["chart_specs"]]
    top_summaries = [item.get("summary", "") for item in state["intermediate_findings"]]
    return {
        "title": f"Draft Report: {state['question']}",
        "analysis_goal": state["analysis_goal"],
        "metric_labels": metric_labels,
        "chart_labels": chart_labels,
        "finding_summaries": top_summaries,
        "draft_status": "ready_for_final_report",
    }


def generate_report_node(state: AnalysisGraphState) -> AnalysisGraphState:
    llm_client = get_llm_client()
    state["draft_report"] = _build_draft_report(state)
    state["completed_steps"].append("draft_report_prepared")
    _persist_state(state)
    tool_request = {
        "question": state["question"],
        "analysis_goal": state["analysis_goal"],
        "tool_results": state["tool_results"],
        "chart_specs": state["chart_specs"],
    }
    record_tool_called(state["task_id"], "generate_report", tool_request)
    report_response = invoke_tool_with_retry("generate_report", **tool_request)
    record_tool_call(state["task_id"], "generate_report", tool_request, report_response.model_dump())
    baseline_report = report_response.data or {}
    llm_report = llm_client.generate_report(
        analysis_goal=state["analysis_goal"],
        intermediate_findings=state["intermediate_findings"],
        chart_specs=state["chart_specs"],
        business_context=state["business_context"],
    )
    state["final_report"] = FinalReport.model_validate(llm_report or baseline_report).model_dump()
    state["completed_steps"].append("generate_report")
    record_report_generated(state["task_id"], state["final_report"])
    return state


def evaluate_report_node(state: AnalysisGraphState) -> AnalysisGraphState:
    llm_client = get_llm_client()
    state["current_step"] = "completed"
    state["status"] = "completed"
    record_task_completed(state["task_id"], "langgraph")
    hydrate_state_events(state)
    state["llm_judgement"] = llm_client.judge_report(
        state["question"],
        state["final_report"],
        state["tool_results"],
    )
    state["eval_result"] = score_task_state(state)
    record_eval_result(state["task_id"], state["eval_result"])
    record_eval_finished(state["task_id"], "langgraph", state["eval_result"])
    hydrate_state_events(state)
    _persist_state(state)
    return state
