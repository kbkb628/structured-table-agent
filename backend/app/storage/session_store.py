import json
import logging

from app.storage.analysis_store import get_task_state
from app.storage.analysis_store import update_task_state

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None

logger = logging.getLogger(__name__)


class SessionStore:
    def __init__(self, url: str = "redis://127.0.0.1:6379/0"):
        self._url = url

    def _build_keys(self, task_id: str) -> dict[str, str]:
        return {
            "analysis_state": f"analysis_state:{task_id}",
            "draft_report": f"draft_report:{task_id}",
            "intermediate_findings": f"intermediate_findings:{task_id}",
            "latest_context": f"latest_context:{task_id}",
        }

    def _connect(self):
        if redis is None:
            return None
        try:
            client = redis.Redis.from_url(self._url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    def load_state(self, task_id: str) -> tuple[dict | None, bool]:
        client = self._connect()
        if client is not None:
            keys = self._build_keys(task_id)
            payload = client.get(keys["analysis_state"])
            state = json.loads(payload) if payload else None
            if state is not None:
                draft_report = client.get(keys["draft_report"])
                intermediate_findings = client.get(keys["intermediate_findings"])
                latest_context = client.get(keys["latest_context"])
                if draft_report:
                    state["draft_report"] = json.loads(draft_report)
                if intermediate_findings:
                    state["intermediate_findings"] = json.loads(intermediate_findings)
                if latest_context:
                    state["business_context"] = json.loads(latest_context)
            return (state, True)
        logger.warning("Redis unavailable; falling back to SQLite-backed session state for task %s", task_id)
        return get_task_state(task_id), False

    def save_state(self, task_id: str, state: dict) -> bool:
        client = self._connect()
        if client is not None:
            keys = self._build_keys(task_id)
            client.set(keys["analysis_state"], json.dumps(state, ensure_ascii=False))
            client.set(keys["draft_report"], json.dumps(state.get("draft_report", {}), ensure_ascii=False))
            client.set(
                keys["intermediate_findings"],
                json.dumps(state.get("intermediate_findings", []), ensure_ascii=False),
            )
            client.set(keys["latest_context"], json.dumps(state.get("business_context", []), ensure_ascii=False))
            update_task_state(task_id, state)
            return True
        logger.warning("Redis unavailable; persisting session state to SQLite for task %s", task_id)
        update_task_state(task_id, state)
        return False
