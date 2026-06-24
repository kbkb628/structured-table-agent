from typing import Any

from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.core import config
from app.schemas.file_schema import FileProfile
from app.schemas.report_schema import FinalReport


class ToolError(BaseModel):
    code: str
    message: str
    suggested_fields: list[str] = []


class ToolResponse(BaseModel):
    success: bool
    tool_name: str
    data: dict[str, Any] | None
    summary: str
    error: ToolError | None
    metadata: dict[str, Any]


class ToolSchemaModel(BaseModel):
    model_config = ConfigDict(strict=True)


class ProfileDatasetArgs(ToolSchemaModel):
    csv_path: Path
    file_id: str = ""
    created_at: str = ""
    filename: str | None = None


class MatchFieldsArgs(ToolSchemaModel):
    question: str
    file_profile: dict[str, Any]


class GroupByAggregateArgs(ToolSchemaModel):
    file_id: str
    group_by: str
    metric_column: str
    aggregation: str
    sort_order: str
    limit: int = 10


class CalculateShareArgs(ToolSchemaModel):
    file_id: str
    group_by: str
    metric_column: str
    aggregation: str
    sort_order: str
    limit: int = 10


class TrendAnalysisArgs(ToolSchemaModel):
    file_id: str
    group_by: str
    metric_column: str
    aggregation: str
    sort_order: str
    limit: int = 10


class AnomalyAnalysisArgs(ToolSchemaModel):
    file_id: str
    group_by: str
    metric_column: str
    aggregation: str
    sort_order: str
    limit: int = 10


class GenerateChartArgs(ToolSchemaModel):
    title: str
    x_field: str
    y_field: str
    rows: list[dict[str, Any]]
    chart_type: str = "bar"


class GenerateReportArgs(ToolSchemaModel):
    question: str
    analysis_goal: str
    tool_result: dict[str, Any] | None = None
    chart_spec: dict[str, Any] | None = None
    tool_results: list[dict[str, Any]] | None = None
    chart_specs: list[dict[str, Any]] | None = None


class AdvancedCodeExecutionArgs(ToolSchemaModel):
    file_id: str
    python_code: str | None = None
    template_name: str | None = None
    timeout_seconds: int | None = None

    @field_validator("python_code")
    @classmethod
    def validate_python_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) > config.DOCKER_SANDBOX_MAX_CODE_CHARS:
            raise ValueError("python_code exceeds the configured sandbox code limit.")
        return value

    @model_validator(mode="after")
    def validate_execution_mode(self):
        if bool(self.python_code) == bool(self.template_name):
            raise ValueError("Provide exactly one of python_code or template_name.")
        return self

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout_seconds(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value < 1 or value > config.DOCKER_SANDBOX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds exceeds the configured sandbox limit.")
        return value


class PlannedToolCall(BaseModel):
    tool_name: str
    group_by: str
    metric_column: str
    aggregation: str
    sort_order: str
    limit: int
    label: str


class MatchMetricSpec(BaseModel):
    metric_field: str
    aggregation: str
    label: str


class MatchFieldsOutput(BaseModel):
    dimension_field: str | None
    metric_field: str | None
    aggregation: str
    analysis_type: str
    metrics: list[MatchMetricSpec]
    planned_tool_calls: list[PlannedToolCall]
    planned_tool_sequence: list[str]
    candidate_fields: list[str]
    warnings: list[str]


class AggregateRowsOutput(BaseModel):
    rows: list[dict[str, Any]]


class ShareRowsOutput(BaseModel):
    rows: list[dict[str, Any]]


class AnomalyRowsOutput(BaseModel):
    rows: list[dict[str, Any]]


class PlotlyAxisTitle(BaseModel):
    title: str


class PlotlyLayout(BaseModel):
    title: str
    xaxis: PlotlyAxisTitle
    yaxis: PlotlyAxisTitle


class PlotlyBarTrace(BaseModel):
    type: str
    x: list[Any]
    y: list[Any]
    mode: str | None = None


class PlotlySpec(BaseModel):
    data: list[PlotlyBarTrace]
    layout: PlotlyLayout


class GenerateChartOutput(BaseModel):
    chart_type: str
    plotly_spec: PlotlySpec
    figure_backend: str
    plotly_trace_count: int


class AdvancedCodeExecutionOutput(BaseModel):
    status: str
    exit_code: int | None
    stdout: str
    stderr: str
    elapsed_ms: int
    parsed_output: dict[str, Any]
    degraded: bool = False


TOOL_DATA_SCHEMAS = {
    "profile_dataset": FileProfile,
    "match_fields": MatchFieldsOutput,
    "groupby_aggregate": AggregateRowsOutput,
    "calculate_share": ShareRowsOutput,
    "trend_analysis": AggregateRowsOutput,
    "anomaly_analysis": AnomalyRowsOutput,
    "generate_chart": GenerateChartOutput,
    "advanced_code_execution": AdvancedCodeExecutionOutput,
    "generate_report": FinalReport,
}
