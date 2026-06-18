from app.schemas.report_schema import FinalReport
from app.schemas.tool_schema import ToolResponse


def _split_top_row(top_row: dict) -> tuple[str, str, object]:
    dimension_key = next(
        (
            key
            for key in top_row
            if not key.endswith(("_sum", "_avg", "_count", "_min", "_max"))
        ),
        "dimension",
    )
    metric_key = next(
        (
            key
            for key in top_row
            if key.endswith(("_sum", "_avg", "_count", "_min", "_max"))
        ),
        "metric",
    )
    return dimension_key, metric_key, top_row.get(metric_key, 0)


def _chart_explanation(chart_type: str) -> str:
    label = "Line" if chart_type == "line" else "Bar"
    return f"{label} chart generated for {chart_type} view."


def _build_key_finding(result: dict, rows: list[dict]) -> dict:
    top_row = rows[0]
    tool_name = result["tool_name"]
    dimension_key, metric_key, metric_value = _split_top_row(top_row)
    top_dimension = top_row.get(dimension_key, "unknown")

    if tool_name == "calculate_share" and "share_percent" in top_row:
        return {
            "finding": f"{top_dimension} contributes the highest grouped share in the current result set",
            "evidence": f"The top grouped share row is {top_dimension} with share_percent = {top_row['share_percent']}",
            "source_tool": tool_name,
        }

    if tool_name == "trend_analysis":
        first_row = rows[0]
        last_row = rows[-1]
        date_key = next((key for key in first_row.keys() if key != metric_key), "dimension")
        return {
            "finding": f"{metric_key} changes over time across the available dates",
            "evidence": (
                f"The time series spans from {date_key} = {first_row.get(date_key)} with {metric_key} = {first_row.get(metric_key)} "
                f"to {date_key} = {last_row.get(date_key)} with {metric_key} = {last_row.get(metric_key)}"
            ),
            "source_tool": tool_name,
        }

    if tool_name == "anomaly_analysis" and "z_score" in top_row:
        return {
            "finding": f"{top_dimension} is the most prominent anomaly in the current result set",
            "evidence": f"The top anomaly row is {top_dimension} with z_score = {top_row['z_score']}",
            "source_tool": tool_name,
        }

    return {
        "finding": f"{top_dimension} performs best in the current result set",
        "evidence": f"The top row in the aggregation result is {top_dimension} with {metric_key} = {metric_value}",
        "source_tool": tool_name,
    }


def generate_report(
    question: str,
    analysis_goal: str,
    tool_result: dict | None = None,
    chart_spec: dict | None = None,
    tool_results: list[dict] | None = None,
    chart_specs: list[dict] | None = None,
) -> dict:
    resolved_tool_results = tool_results or ([tool_result] if tool_result else [])
    resolved_chart_specs = chart_specs or ([chart_spec] if chart_spec else [])
    key_findings: list[dict] = []

    for result in resolved_tool_results:
        rows = result.get("data", {}).get("rows", [])
        if not rows:
            continue

        key_findings.append(_build_key_finding(result, rows))

    if not key_findings:
        key_findings.append(
            {
                "finding": "No non-empty aggregation result was available for reporting",
                "evidence": "The task did not produce any populated tool result rows.",
                "source_tool": "report_builder",
            }
        )

    report = {
        "title": f"Analysis Report: {question}",
        "analysis_goal": analysis_goal,
        "key_findings": key_findings,
        "chart_explanations": [
            _chart_explanation(item["chart_type"])
            for item in resolved_chart_specs
        ]
        or ["No chart was generated; conclusions are based on tabular tool results."],
        "business_suggestions": ["Review the top-performing segment and compare it against weaker segments."],
        "data_limitations": ["This report reflects the uploaded CSV and the matched fields only."],
        "next_steps": ["Validate whether additional segmentation is needed for deeper analysis."],
    }
    validated_report = FinalReport.model_validate(report)
    return ToolResponse(
        success=True,
        tool_name="generate_report",
        data=validated_report.model_dump(),
        summary="generated a structured analysis report from tool outputs",
        error=None,
        metadata={"tool_result_count": len(resolved_tool_results), "chart_count": len(resolved_chart_specs)},
    )
