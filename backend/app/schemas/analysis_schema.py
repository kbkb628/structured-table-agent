from typing import Any

from pydantic import BaseModel

from app.schemas.event_schema import AnalysisEvent


class AnalysisStartRequest(BaseModel):
    file_id: str
    question: str


class AnalysisStartResponse(BaseModel):
    task_id: str
    status: str
    analysis_goal: str
    analysis_plan: list[str]
    business_context: list[dict[str, Any]]


class AnalysisTaskState(BaseModel):
    task_id: str
    file_id: str
    question: str
    analysis_goal: str
    file_profile: dict[str, Any]
    field_understanding: dict[str, Any]
    business_context: list[dict[str, Any]]
    analysis_plan: list[str]
    current_step: str
    completed_steps: list[str]
    intermediate_findings: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    chart_specs: list[dict[str, Any]]
    draft_report: dict[str, Any]
    final_report: dict[str, Any]
    eval_result: dict[str, Any]
    events: list[AnalysisEvent]
    errors: list[dict[str, Any]]
    status: str


class EvalRunRequest(BaseModel):
    task_id: str


class EvalRunResponse(BaseModel):
    task_id: str
    eval_result: dict[str, Any]
