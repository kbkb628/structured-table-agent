from app.agent.graph import run_analysis_graph
from app.observability.event_logger import record_session_store_warning
from app.storage.session_store import SessionStore


def run_analysis_task(task_id: str) -> dict:
    session_store = SessionStore()
    _, used_redis = session_store.load_state(task_id)
    if not used_redis:
        record_session_store_warning(
            task_id,
            {"backend": "sqlite", "reason": "redis unavailable or redis package not installed"},
        )
    return run_analysis_graph(task_id)
