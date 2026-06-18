from app.agent.graph import run_analysis_graph
from app.observability.event_logger import hydrate_state_events
from app.observability.event_logger import record_session_store_warning
from app.storage.analysis_store import get_tool_call_logs
from app.storage.session_store import SessionStore


def run_analysis_task(task_id: str) -> dict:
    session_store = SessionStore()
    with session_store.task_lock(task_id):
        _, used_redis = session_store.load_state(task_id)
        if not used_redis:
            record_session_store_warning(
                task_id,
                {"backend": "sqlite", "reason": "redis unavailable or redis package not installed"},
            )
        state = run_analysis_graph(task_id)
        hydrate_state_events(state)
        state["tool_call_logs"] = get_tool_call_logs(task_id)
        if "context_checkpoint" not in state:
            state["context_checkpoint"] = session_store._build_context_checkpoint(state)
        return state
