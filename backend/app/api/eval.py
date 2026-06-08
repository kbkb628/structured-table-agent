from fastapi import APIRouter, HTTPException

from app.eval.rule_scorer import score_task_state
from app.schemas.analysis_schema import EvalRunRequest, EvalRunResponse
from app.storage.analysis_store import get_task_state, list_task_events, record_eval_result, record_event, update_task_state

router = APIRouter(prefix="/api/eval", tags=["eval"])


@router.post("/run", response_model=EvalRunResponse)
def run_eval(request: EvalRunRequest) -> EvalRunResponse:
    state = get_task_state(request.task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    state["events"] = list_task_events(request.task_id)
    eval_result = score_task_state(state)
    state["eval_result"] = eval_result
    record_eval_result(request.task_id, eval_result)
    record_event(request.task_id, "eval_finished", "run_eval", "rule evaluation completed", eval_result)
    state["events"] = list_task_events(request.task_id)
    update_task_state(request.task_id, state)
    return EvalRunResponse(task_id=request.task_id, eval_result=eval_result)
