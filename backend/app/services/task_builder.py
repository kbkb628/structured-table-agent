import json
import uuid

from app.llm.base import LLMClient
from app.llm.mock_client import MockLLMClient
from app.observability.event_logger import record_startup_events
from app.rag.keyword_retriever import retrieve_business_context
from app.storage.analysis_store import create_task
from app.storage.file_store import get_file_record
from app.storage.session_store import SessionStore


def build_file_profile_from_record(file_id: str) -> dict | None:
    file_record = get_file_record(file_id)
    if file_record is None:
        return None

    return {
        "file_id": file_record.file_id,
        "filename": file_record.filename,
        "row_count": file_record.row_count,
        "column_count": file_record.column_count,
        "columns": json.loads(file_record.columns_json),
        "created_at": file_record.created_at,
    }


def build_analysis_state(
    task_id: str,
    file_id: str,
    question: str,
    file_profile: dict,
    llm_client: LLMClient | None = None,
) -> tuple[dict, list[dict], str, list[str]]:
    client = llm_client or MockLLMClient()
    business_context = retrieve_business_context(question, file_profile)["items"]
    analysis_goal = client.generate_analysis_goal(question, file_profile, business_context)
    analysis_plan = client.generate_analysis_plan(analysis_goal, file_profile, business_context)

    state = {
        "task_id": task_id,
        "file_id": file_id,
        "question": question,
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
    return state, business_context, analysis_goal, analysis_plan


def create_analysis_task(
    file_id: str,
    question: str,
    source_node: str,
    file_profile: dict,
    task_id: str | None = None,
    llm_client: LLMClient | None = None,
) -> tuple[str, dict]:
    resolved_task_id = task_id or f"task_{uuid.uuid4().hex[:12]}"
    state, business_context, analysis_goal, analysis_plan = build_analysis_state(
        task_id=resolved_task_id,
        file_id=file_id,
        question=question,
        file_profile=file_profile,
        llm_client=llm_client,
    )
    create_task(resolved_task_id, file_id, question, state)
    SessionStore().save_state(resolved_task_id, state)
    record_startup_events(
        resolved_task_id,
        source_node,
        file_profile,
        business_context,
        analysis_goal,
        analysis_plan,
    )
    return resolved_task_id, state
