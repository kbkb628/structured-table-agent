from fastapi import APIRouter, HTTPException

from app.eval.eval_cases import run_fixed_eval_cases
from app.eval.rule_scorer import score_task_state
from app.observability.event_logger import hydrate_state_events
from app.observability.event_logger import record_eval_finished
from app.schemas.analysis_schema import EvalCasesRunResponse
from app.schemas.analysis_schema import EvalRunRequest, EvalRunResponse
from app.storage.analysis_store import record_eval_result
from app.storage.session_store import SessionStore

router = APIRouter(prefix="/api/eval", tags=["eval"])


@router.post("/run", response_model=EvalRunResponse)
def run_eval(request: EvalRunRequest) -> EvalRunResponse:
    state, _ = SessionStore().load_state(request.task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    hydrate_state_events(state)
    eval_result = score_task_state(state)
    llm_judgement = state.get("llm_judgement") or {}
    eval_result["judge_status"] = llm_judgement.get("judge_status")
    eval_result["judge_degraded"] = bool(llm_judgement.get("degraded"))
    eval_result["judge_summary"] = llm_judgement.get("judge_summary")
    eval_result["judge_issue_count"] = int(llm_judgement.get("issue_count", 0) or 0)
    state["eval_result"] = eval_result
    record_eval_result(request.task_id, eval_result)
    record_eval_finished(request.task_id, "run_eval", eval_result)
    hydrate_state_events(state)
    SessionStore().save_state(request.task_id, state)
    return EvalRunResponse(task_id=request.task_id, eval_result=eval_result)


@router.post("/cases/run", response_model=EvalCasesRunResponse)
def run_eval_cases() -> EvalCasesRunResponse:
    return EvalCasesRunResponse(**run_fixed_eval_cases())
