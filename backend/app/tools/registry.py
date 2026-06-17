from collections.abc import Callable

from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse
from app.tools.chart_tool import generate_chart
from app.tools.duckdb_tools import groupby_aggregate
from app.tools.match_fields import match_fields
from app.tools.report_tool import generate_report


ToolCallable = Callable[..., ToolResponse]


def invoke_tool(tool_name: str, **kwargs) -> ToolResponse:
    registry = get_tool_registry()
    if tool_name not in registry:
        return ToolResponse(
            success=False,
            tool_name=tool_name,
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="TOOL_NOT_FOUND",
                message=f"Tool {tool_name} is not registered",
                suggested_fields=[],
            ),
            metadata={},
        )
    return registry[tool_name](**kwargs)


def get_tool_registry() -> dict[str, ToolCallable]:
    return {
        "match_fields": match_fields,
        "groupby_aggregate": groupby_aggregate,
        "generate_chart": generate_chart,
        "generate_report": generate_report,
    }
