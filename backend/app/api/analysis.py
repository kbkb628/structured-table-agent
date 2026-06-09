import json
import uuid

from fastapi import APIRouter, HTTPException

from app.llm.mock_client import MockLLMClient
from app.rag.keyword_retriever import retrieve_business_context
from app.schemas.analysis_schema import AnalysisStartRequest, AnalysisStartResponse, AnalysisTaskState
from app.schemas.event_schema import AnalysisEventList
from app.services.analysis_runner import run_analysis_task
from app.storage.analysis_store import create_task, get_task_state, list_task_events, record_event
from app.storage.file_store import get_file_record

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/start", response_model=AnalysisStartResponse)
def start_analysis(request: AnalysisStartRequest) -> AnalysisStartResponse:
    file_record = get_file_record(request.file_id)
    if file_record is None:
        raise HTTPException(status_code=404, detail="File not found.")

    task_id = f"task_{uuid.uuid4().hex[:12]}"
    file_profile = {
        "file_id": file_record.file_id,
        "filename": file_record.filename,
        "row_count": file_record.row_count,
        "column_count": file_record.column_count,
        "columns": json.loads(file_record.columns_json),
        "created_at": file_record.created_at,
    }
    business_context = retrieve_business_context(request.question, file_profile)["items"]
    llm_client = MockLLMClient()
    analysis_goal = llm_client.generate_analysis_goal(request.question, file_profile, business_context)
    analysis_plan = llm_client.generate_analysis_plan(analysis_goal, file_profile, business_context)
    state = {
        "task_id": task_id,
        "file_id": request.file_id,
        "question": request.question,
        "analysis_goal": analysis_goal,
        "file_profile": file_profile,
        "field_understanding": {},
        "business_context": business_context,
        "analysis_plan": analysis_plan,
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }
    create_task(task_id, request.file_id, request.question, state)
    record_event(task_id, "task_created", "start_analysis", "task created", {"status": "created"})
    record_event(
        task_id,
        "rag_retrieved",
        "start_analysis",
        "business context retrieved",
        {"item_count": len(business_context), "item_ids": [item["id"] for item in business_context]},
    )
    record_event(
        task_id,
        "goal_understood",
        "start_analysis",
        "analysis goal generated",
        {"analysis_goal": analysis_goal},
    )
    record_event(
        task_id,
        "plan_generated",
        "start_analysis",
        "analysis plan generated",
        {"analysis_plan": analysis_plan},
    )
    return AnalysisStartResponse(
        task_id=task_id,
        status="created",
        analysis_goal=analysis_goal,
        analysis_plan=analysis_plan,
        business_context=business_context,
    )


@router.post("/{task_id}/run", response_model=AnalysisTaskState)
def run_analysis(task_id: str) -> AnalysisTaskState:
    state = get_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return AnalysisTaskState(**run_analysis_task(task_id))


@router.get("/{task_id}", response_model=AnalysisTaskState)
def get_analysis(task_id: str) -> AnalysisTaskState:
    state = get_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    state["events"] = list_task_events(task_id)
    return AnalysisTaskState(**state)


@router.get("/{task_id}/events", response_model=AnalysisEventList)
def get_analysis_events(task_id: str) -> AnalysisEventList:
    state = get_task_state(task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return AnalysisEventList(task_id=task_id, events=list_task_events(task_id))
