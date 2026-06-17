import json

from app.storage.analysis_store import get_task_state
from app.storage.analysis_store import update_task_state

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None


class SessionStore:
    def __init__(self, url: str = "redis://127.0.0.1:6379/0"):
        self._url = url

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
            payload = client.get(f"analysis_state:{task_id}")
            return (json.loads(payload) if payload else None, True)
        return get_task_state(task_id), False

    def save_state(self, task_id: str, state: dict) -> bool:
        client = self._connect()
        if client is not None:
            client.set(f"analysis_state:{task_id}", json.dumps(state, ensure_ascii=False))
            update_task_state(task_id, state)
            return True
        update_task_state(task_id, state)
        return False
