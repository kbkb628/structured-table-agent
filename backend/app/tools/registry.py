from collections.abc import Callable

from pydantic import ValidationError

from app.schemas.tool_schema import CalculateShareArgs
from app.schemas.tool_schema import AnomalyAnalysisArgs
from app.schemas.tool_schema import GenerateChartArgs
from app.schemas.tool_schema import GenerateReportArgs
from app.schemas.tool_schema import GroupByAggregateArgs
from app.schemas.tool_schema import MatchFieldsArgs
from app.schemas.tool_schema import ProfileDatasetArgs
from app.schemas.tool_schema import TrendAnalysisArgs
from app.schemas.tool_schema import TOOL_DATA_SCHEMAS
from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse
from app.tools.chart_tool import generate_chart
from app.tools.anomaly_tool import anomaly_analysis
from app.tools.data_profile import profile_dataset
from app.tools.duckdb_tools import groupby_aggregate
from app.tools.match_fields import match_fields
from app.tools.report_tool import generate_report
from app.tools.share_tool import calculate_share
from app.tools.trend_tool import trend_analysis


ToolCallable = Callable[..., ToolResponse]


TOOL_ARG_SCHEMAS = {
    "profile_dataset": ProfileDatasetArgs,
    "match_fields": MatchFieldsArgs,
    "groupby_aggregate": GroupByAggregateArgs,
    "calculate_share": CalculateShareArgs,
    "trend_analysis": TrendAnalysisArgs,
    "anomaly_analysis": AnomalyAnalysisArgs,
    "generate_chart": GenerateChartArgs,
    "generate_report": GenerateReportArgs,
}


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

    schema = TOOL_ARG_SCHEMAS.get(tool_name)
    if schema is not None:
        try:
            validated_args = schema.model_validate(kwargs)
        except ValidationError as exc:
            return ToolResponse(
                success=False,
                tool_name=tool_name,
                data=None,
                summary="tool argument validation failed",
                error=ToolError(
                    code="TOOL_ARGUMENT_VALIDATION_FAILED",
                    message=str(exc),
                    suggested_fields=[],
                ),
                metadata={"validation_error_count": len(exc.errors())},
            )
        kwargs = validated_args.model_dump()

    raw_response = registry[tool_name](**kwargs)
    try:
        validated_response = ToolResponse.model_validate(raw_response)
    except ValidationError as exc:
        return ToolResponse(
            success=False,
            tool_name=tool_name,
            data=None,
            summary="tool response validation failed",
            error=ToolError(
                code="TOOL_RESPONSE_VALIDATION_FAILED",
                message=str(exc),
                suggested_fields=[],
            ),
            metadata={"validation_error_count": len(exc.errors())},
        )

    data_schema = TOOL_DATA_SCHEMAS.get(tool_name)
    if data_schema is not None and validated_response.data is not None:
        try:
            validated_response.data = data_schema.model_validate(validated_response.data).model_dump()
        except ValidationError as exc:
            return ToolResponse(
                success=False,
                tool_name=tool_name,
                data=None,
                summary="tool data validation failed",
                error=ToolError(
                    code="TOOL_DATA_VALIDATION_FAILED",
                    message=str(exc),
                    suggested_fields=[],
                ),
                metadata={"validation_error_count": len(exc.errors())},
            )

    return validated_response


def invoke_tool_with_retry(tool_name: str, max_retries: int = 1, **kwargs) -> ToolResponse:
    attempts = 0
    response = invoke_tool(tool_name, **kwargs)
    while attempts < max_retries and not response.success:
        attempts += 1
        response = invoke_tool(tool_name, **kwargs)

    merged_metadata = dict(response.metadata or {})
    merged_metadata["retry_attempts"] = attempts
    if attempts == 0:
        merged_metadata["retry_status"] = "not_needed"
    elif response.success:
        merged_metadata["retry_status"] = "recovered"
    else:
        merged_metadata["retry_status"] = "exhausted"
    response.metadata = merged_metadata
    return response


def get_tool_registry() -> dict[str, ToolCallable]:
    return {
        "profile_dataset": profile_dataset,
        "match_fields": match_fields,
        "groupby_aggregate": groupby_aggregate,
        "calculate_share": calculate_share,
        "trend_analysis": trend_analysis,
        "anomaly_analysis": anomaly_analysis,
        "generate_chart": generate_chart,
        "generate_report": generate_report,
    }
