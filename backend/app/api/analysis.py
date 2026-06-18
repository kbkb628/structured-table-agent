from fastapi import APIRouter, HTTPException

from app.llm.factory import LLMConfigurationError
from app.llm.qwen_client import QwenResponseError
from app.observability.event_logger import list_analysis_events
from app.schemas.analysis_schema import AnalysisStartRequest, AnalysisStartResponse, AnalysisTaskState
from app.schemas.analysis_schema import AnalysisToolLogList
from app.schemas.event_schema import AnalysisEventList
from app.services.task_builder import build_file_profile_from_record
from app.services.task_builder import create_analysis_task
from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import get_task_state, get_tool_call_logs
from app.storage.session_store import SessionStore

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/start", response_model=AnalysisStartResponse)
def start_analysis(request: AnalysisStartRequest) -> AnalysisStartResponse:
    file_profile = build_file_profile_from_record(request.file_id)
    if file_profile is None:
        raise HTTPException(status_code=404, detail="File not found.")

    try:
        task_id, state = create_analysis_task(
            file_id=request.file_id,
            question=request.question,
            source_node="start_analysis",
            file_profile=file_profile,
        )
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except QwenResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AnalysisStartResponse(
        task_id=task_id,
        status="created",
        analysis_goal=state["analysis_goal"],
        analysis_plan=state["analysis_plan"],
    )


@router.post("/{task_id}/run", response_model=AnalysisTaskState)
def run_analysis(task_id: str) -> AnalysisTaskState:
    state = get_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    try:
        return AnalysisTaskState(**run_analysis_task(task_id))
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{task_id}", response_model=AnalysisTaskState)
def get_analysis(task_id: str) -> AnalysisTaskState:
    state, _ = SessionStore().load_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    persisted_events = list_analysis_events(task_id)
    if persisted_events or not state.get("events"):
        state["events"] = persisted_events
    state["tool_call_logs"] = get_tool_call_logs(task_id)
    if "context_checkpoint" not in state:
        state["context_checkpoint"] = SessionStore()._build_context_checkpoint(state)
    return AnalysisTaskState(**state)


@router.get("/{task_id}/events", response_model=AnalysisEventList)
def get_analysis_events(task_id: str) -> AnalysisEventList:
    state = get_task_state(task_id)
    if state is None:
        state, _ = SessionStore().load_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return AnalysisEventList(task_id=task_id, events=list_analysis_events(task_id))


@router.get("/{task_id}/tool-logs", response_model=AnalysisToolLogList)
def get_analysis_tool_logs(task_id: str) -> AnalysisToolLogList:
    state = get_task_state(task_id)
    if state is None:
        state, _ = SessionStore().load_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return AnalysisToolLogList(task_id=task_id, tool_call_logs=get_tool_call_logs(task_id))
