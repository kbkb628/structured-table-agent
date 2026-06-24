import plotly.graph_objects as go

from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse


def _normalize_plotly_spec(
    raw_plotly_spec: dict,
    title: str,
    x_field: str,
    y_field: str,
) -> dict:
    traces = []
    for trace in raw_plotly_spec.get("data", []):
        normalized_trace = {
            "type": trace.get("type"),
            "x": trace.get("x", []),
            "y": trace.get("y", []),
        }
        if trace.get("mode") is not None:
            normalized_trace["mode"] = trace["mode"]
        traces.append(normalized_trace)

    layout = raw_plotly_spec.get("layout", {})
    title_value = layout.get("title", {})
    if isinstance(title_value, dict):
        title_text = title_value.get("text", title)
    else:
        title_text = title_value or title

    xaxis = layout.get("xaxis", {})
    xaxis_title = xaxis.get("title", {})
    if isinstance(xaxis_title, dict):
        xaxis_title_text = xaxis_title.get("text", x_field)
    else:
        xaxis_title_text = xaxis_title or x_field

    yaxis = layout.get("yaxis", {})
    yaxis_title = yaxis.get("title", {})
    if isinstance(yaxis_title, dict):
        yaxis_title_text = yaxis_title.get("text", y_field)
    else:
        yaxis_title_text = yaxis_title or y_field

    return {
        "data": traces,
        "layout": {
            "title": title_text,
            "xaxis": {"title": xaxis_title_text},
            "yaxis": {"title": yaxis_title_text},
        },
    }


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

    x_values = [row[x_field] for row in rows]
    y_values = [row[y_field] for row in rows]
    if chart_type == "line":
        figure = go.Figure(
            data=[go.Scatter(x=x_values, y=y_values, mode="lines+markers")]
        )
    else:
        figure = go.Figure(
            data=[go.Bar(x=x_values, y=y_values)]
        )
    figure.update_layout(title=title, xaxis_title=x_field, yaxis_title=y_field)
    raw_plotly_spec = figure.to_plotly_json()
    plotly_spec = _normalize_plotly_spec(
        raw_plotly_spec=raw_plotly_spec,
        title=title,
        x_field=x_field,
        y_field=y_field,
    )

    return ToolResponse(
        success=True,
        tool_name="generate_chart",
        data={
            "chart_type": chart_type,
            "plotly_spec": plotly_spec,
            "figure_backend": "plotly",
            "plotly_trace_count": len(raw_plotly_spec.get("data", [])),
        },
        summary=f"generated Plotly {chart_type} figure from grouped rows",
        error=None,
        metadata={
            "row_count": len(rows),
            "fields_used": [x_field, y_field],
            "chart_type": chart_type,
            "figure_backend": "plotly",
        },
    )
