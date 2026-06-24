from typing import Any

from pydantic import BaseModel, Field

from app.schemas.event_schema import AnalysisEvent


class AnalysisStartRequest(BaseModel):
    file_id: str
    question: str


class AnalysisStartResponse(BaseModel):
    task_id: str
    status: str
    analysis_goal: str
    analysis_plan: list[str]


class ToolCallLog(BaseModel):
    log_id: str
    task_id: str
    tool_name: str
    request_json: str
    response_json: str
    success: bool
    elapsed_ms: int
    created_at: str


class AnalysisToolLogList(BaseModel):
    task_id: str
    tool_call_logs: list[ToolCallLog]


class AnalysisTaskState(BaseModel):
    task_id: str
    file_id: str
    question: str
    analysis_goal: str
    file_profile: dict[str, Any]
    field_understanding: dict[str, Any]
    business_context: list[dict[str, Any]]
    memory_context: dict[str, Any] = Field(default_factory=dict)
    analysis_plan: list[str]
    current_step: str
    completed_steps: list[str]
    intermediate_findings: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    chart_specs: list[dict[str, Any]]
    draft_report: dict[str, Any]
    final_report: dict[str, Any]
    llm_judgement: dict[str, Any] = Field(default_factory=dict)
    eval_result: dict[str, Any]
    events: list[AnalysisEvent]
    errors: list[dict[str, Any]]
    status: str
    pending_metrics: list[dict[str, Any]] = Field(default_factory=list)
    pending_tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    context_checkpoint: dict[str, Any] = Field(default_factory=dict)
    tool_call_logs: list[ToolCallLog] = Field(default_factory=list)


class EvalRunRequest(BaseModel):
    task_id: str


class EvalRunResponse(BaseModel):
    task_id: str
    eval_result: dict[str, Any]


class EvalCasesRunResponse(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    retried_tool_calls: int
    retry_attempts_total: int
    average_tool_success_rate: float
    average_tool_elapsed_ms_total: float
    average_trace_completeness: float
    average_report_completeness: float
    average_chart_validity: float
    average_field_validity: float
    results: list[dict[str, Any]]


class LLMProviderDiagnostics(BaseModel):
    provider_supported: bool
    key_source_kind: str
    smoke_ready: bool
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class LLMProviderStatusResponse(BaseModel):
    provider: str
    allow_fallback: bool
    has_api_key: bool
    api_key_source: str | None
    base_url: str
    model: str
    timeout_seconds: float
    diagnostics: LLMProviderDiagnostics


class LLMProviderSmokeResponse(BaseModel):
    provider_resolution: LLMProviderStatusResponse
    client_type: str | None = None
    ok: bool
    analysis_goal: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    diagnostics: LLMProviderDiagnostics
