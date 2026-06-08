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

        top_row = rows[0]
        dimension_key, metric_key, metric_value = _split_top_row(top_row)
        top_dimension = top_row.get(dimension_key, "unknown")
        key_findings.append(
            {
                "finding": f"{top_dimension} performs best in the current result set",
                "evidence": f"The top row in the aggregation result is {top_dimension} with {metric_key} = {metric_value}",
                "source_tool": result["tool_name"],
            }
        )

    if not key_findings:
        key_findings.append(
            {
                "finding": "No non-empty aggregation result was available for reporting",
                "evidence": "The task did not produce any populated tool result rows.",
                "source_tool": "report_builder",
            }
        )

    return {
        "title": f"Analysis Report: {question}",
        "analysis_goal": analysis_goal,
        "key_findings": key_findings,
        "chart_explanations": [
            f"Bar chart generated for {item['chart_type']} view."
            for item in resolved_chart_specs
        ]
        or ["No chart was generated; conclusions are based on tabular tool results."],
        "business_suggestions": ["Review the top-performing segment and compare it against weaker segments."],
        "data_limitations": ["This report reflects the uploaded CSV and the matched fields only."],
        "next_steps": ["Validate whether additional segmentation is needed for deeper analysis."],
    }
