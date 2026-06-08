def generate_report(question: str, analysis_goal: str, tool_result: dict, chart_spec: dict) -> dict:
    rows = tool_result["data"]["rows"]
    top_row = rows[0] if rows else {}
    top_dimension = next(
        (
            value
            for key, value in top_row.items()
            if not key.endswith(("_sum", "_avg", "_count", "_min", "_max"))
        ),
        "unknown",
    )
    top_metric = next(
        (
            value
            for key, value in top_row.items()
            if key.endswith(("_sum", "_avg", "_count", "_min", "_max"))
        ),
        0,
    )

    return {
        "title": f"Analysis Report: {question}",
        "analysis_goal": analysis_goal,
        "key_findings": [
            {
                "finding": f"{top_dimension} performs best in the current result set",
                "evidence": f"The top row in the aggregation result is {top_dimension} with value {top_metric}",
                "source_tool": tool_result["tool_name"],
            }
        ],
        "chart_explanations": [f"Bar chart generated for {chart_spec['chart_type']} view."],
        "business_suggestions": ["Review the top-performing segment and compare it against weaker segments."],
        "data_limitations": ["This report reflects the uploaded CSV and the matched fields only."],
        "next_steps": ["Validate whether additional segmentation is needed for deeper analysis."],
    }
