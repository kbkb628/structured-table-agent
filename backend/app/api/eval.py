from fastapi import APIRouter, HTTPException

from app.eval.rule_scorer import score_task_state
from app.observability.event_logger import hydrate_state_events
from app.observability.event_logger import record_eval_finished
from app.schemas.analysis_schema import EvalRunRequest, EvalRunResponse
from app.storage.analysis_store import get_task_state, record_eval_result, update_task_state

router = APIRouter(prefix="/api/eval", tags=["eval"])


@router.post("/run", response_model=EvalRunResponse)
def run_eval(request: EvalRunRequest) -> EvalRunResponse:
    state = get_task_state(request.task_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Task not found.")

    hydrate_state_events(state)
    eval_result = score_task_state(state)
    state["eval_result"] = eval_result
    record_eval_result(request.task_id, eval_result)
    record_eval_finished(request.task_id, "run_eval", eval_result)
    hydrate_state_events(state)
    update_task_state(request.task_id, state)
    return EvalRunResponse(task_id=request.task_id, eval_result=eval_result)
