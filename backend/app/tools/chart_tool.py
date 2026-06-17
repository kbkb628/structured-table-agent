from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse


def generate_chart(title: str, x_field: str, y_field: str, rows: list[dict]) -> ToolResponse:
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

    return ToolResponse(
        success=True,
        tool_name="generate_chart",
        data={
            "chart_type": "bar",
            "plotly_spec": {
                "data": [
                    {
                        "type": "bar",
                        "x": [row[x_field] for row in rows],
                        "y": [row[y_field] for row in rows],
                    }
                ],
                "layout": {"title": title, "xaxis": {"title": x_field}, "yaxis": {"title": y_field}},
            },
        },
        summary="generated Plotly bar chart spec from grouped rows",
        error=None,
        metadata={"row_count": len(rows), "fields_used": [x_field, y_field]},
    )
