from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse


def generate_chart(
    title: str,
    x_field: str,
    y_field: str,
    rows: list[dict],
    chart_type: str = "bar",
) -> ToolResponse:
    if not rows:
        return ToolResponse(
            success=False,
            tool_name="generate_chart",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="CHART_GENERATION_FAILED",
                message="Rows cannot be empty for chart generation.",
                suggested_fields=[],
            ),
            metadata={},
        )
    if x_field not in rows[0] or y_field not in rows[0]:
        return ToolResponse(
            success=False,
            tool_name="generate_chart",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="CHART_GENERATION_FAILED",
                message=f"Chart fields {x_field} and {y_field} must exist in row data.",
                suggested_fields=list(rows[0].keys()),
            ),
            metadata={},
        )

    if chart_type not in {"bar", "line"}:
        return ToolResponse(
            success=False,
            tool_name="generate_chart",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="CHART_GENERATION_FAILED",
                message=f"Unsupported chart_type: {chart_type}",
                suggested_fields=["bar", "line"],
            ),
            metadata={},
        )

    trace = {
        "x": [row[x_field] for row in rows],
        "y": [row[y_field] for row in rows],
    }
    if chart_type == "line":
        trace["type"] = "scatter"
        trace["mode"] = "lines+markers"
    else:
        trace["type"] = "bar"

    return ToolResponse(
        success=True,
        tool_name="generate_chart",
        data={
            "chart_type": chart_type,
            "plotly_spec": {
                "data": [trace],
                "layout": {"title": title, "xaxis": {"title": x_field}, "yaxis": {"title": y_field}},
            },
        },
        summary=f"generated Plotly {chart_type} chart spec from grouped rows",
        error=None,
        metadata={"row_count": len(rows), "fields_used": [x_field, y_field], "chart_type": chart_type},
    )
