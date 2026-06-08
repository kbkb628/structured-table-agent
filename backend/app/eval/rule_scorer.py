REQUIRED_REPORT_FIELDS = (
    "title",
    "analysis_goal",
    "key_findings",
    "chart_explanations",
    "business_suggestions",
    "data_limitations",
    "next_steps",
)

REQUIRED_TRACE_EVENTS = (
    "task_created",
    "fields_matched",
    "tool_succeeded",
    "report_generated",
    "task_completed",
)


def _as_bool_score(value: bool) -> float:
    return 1.0 if value else 0.0


def score_task_state(state: dict) -> dict:
    issues: list[str] = []
    suggestions: list[str] = []

    field_understanding = state.get("field_understanding", {})
    tool_results = state.get("tool_results", [])
    chart_specs = state.get("chart_specs", [])
    final_report = state.get("final_report", {})
    events = state.get("events", [])

    schema_valid = all(
        key in state
        for key in ("field_understanding", "tool_results", "chart_specs", "final_report", "events", "status")
    )
    if not schema_valid:
        issues.append("Task state is missing one or more required top-level fields.")
        suggestions.append("Persist the full analysis task state before running evaluation.")

    total_tools = len(tool_results)
    success_count = sum(1 for item in tool_results if item.get("success") is True)
    tool_success_rate = success_count / total_tools if total_tools else 0.0
    if total_tools == 0:
        issues.append("No tool result was available to score.")
        suggestions.append("Run at least one real tool call before evaluating the task.")

    field_validity = bool(field_understanding.get("dimension_field")) and (
        bool(field_understanding.get("metric_field")) or bool(field_understanding.get("metrics"))
    )
    if not field_validity:
        issues.append("Field understanding does not contain an executable dimension/metric match.")
        suggestions.append("Improve field matching so the task can resolve valid analysis fields.")

    has_tool_rows = any(item.get("data", {}).get("rows") for item in tool_results if item.get("success") is True)
    chart_validity = bool(chart_specs) and all(
        item.get("chart_type") and item.get("plotly_spec", {}).get("data")
        for item in chart_specs
    )
    if has_tool_rows and not chart_validity:
        issues.append("Chart output is missing or invalid for a task with non-empty tool results.")
        suggestions.append("Generate at least one valid chart spec or record an explicit chart degradation.")

    completed_report_fields = sum(1 for field in REQUIRED_REPORT_FIELDS if final_report.get(field))
    report_completeness = completed_report_fields / len(REQUIRED_REPORT_FIELDS)
    if report_completeness < 1.0:
        issues.append("Final report is missing one or more required sections.")
        suggestions.append("Populate every required report section before marking the task complete.")

    event_types = {item.get("event_type") for item in events}
    required_trace_events = set(REQUIRED_TRACE_EVENTS)
    if chart_specs:
        required_trace_events.add("chart_generated")
    trace_completeness = len(event_types & required_trace_events) / len(required_trace_events)
    if trace_completeness < 1.0:
        issues.append("Trace is incomplete for the current task lifecycle.")
        suggestions.append("Record the remaining task lifecycle events to improve trace completeness.")

    overall_score = round(
        (
            _as_bool_score(schema_valid)
            + tool_success_rate
            + _as_bool_score(field_validity)
            + _as_bool_score(chart_validity or not has_tool_rows)
            + report_completeness
            + trace_completeness
        )
        / 6,
        2,
    )

    return {
        "overall_score": overall_score,
        "schema_valid": schema_valid,
        "tool_success_rate": round(tool_success_rate, 2),
        "field_validity": field_validity,
        "chart_validity": chart_validity if has_tool_rows else True,
        "report_completeness": round(report_completeness, 2),
        "trace_completeness": round(trace_completeness, 2),
        "issues": issues,
        "suggestions": suggestions,
    }
