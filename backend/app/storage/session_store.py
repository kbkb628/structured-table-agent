import json
import logging
import threading
import time
import uuid
from contextlib import contextmanager

from app.storage.analysis_store import get_task_state
from app.storage.analysis_store import update_task_state

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None

logger = logging.getLogger(__name__)


class SessionStore:
    _memory_locks: dict[str, tuple[str, float | None]] = {}
    _memory_lock = threading.Lock()

    def __init__(self, url: str = "redis://127.0.0.1:6379/0"):
        self._url = url

    def _build_keys(self, task_id: str) -> dict[str, str]:
        return {
            "analysis_state": f"analysis_state:{task_id}",
            "draft_report": f"draft_report:{task_id}",
            "intermediate_findings": f"intermediate_findings:{task_id}",
            "latest_context": f"latest_context:{task_id}",
            "task_lock": f"task_lock:{task_id}",
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

    def acquire_task_lock(self, task_id: str, ttl_seconds: int = 900) -> str | None:
        token = uuid.uuid4().hex
        client = self._connect()
        if client is not None:
            keys = self._build_keys(task_id)
            locked = client.set(keys["task_lock"], token, nx=True, ex=ttl_seconds)
            return token if locked else None

        expires_at = time.monotonic() + ttl_seconds if ttl_seconds > 0 else None
        with self._memory_lock:
            current = self._memory_locks.get(task_id)
            if current is not None:
                _, current_expires_at = current
                if current_expires_at is None or current_expires_at > time.monotonic():
                    return None
                self._memory_locks.pop(task_id, None)
            self._memory_locks[task_id] = (token, expires_at)
        return token

    def release_task_lock(self, task_id: str, token: str) -> bool:
        client = self._connect()
        if client is not None:
            keys = self._build_keys(task_id)
            release_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            end
            return 0
            """
            released = client.eval(release_script, 1, keys["task_lock"], token)
            return bool(released)

        with self._memory_lock:
            current = self._memory_locks.get(task_id)
            if current is None:
                return False
            current_token, _ = current
            if current_token != token:
                return False
            self._memory_locks.pop(task_id, None)
            return True

    @contextmanager
    def task_lock(self, task_id: str, ttl_seconds: int = 900):
        token = self.acquire_task_lock(task_id, ttl_seconds=ttl_seconds)
        if token is None:
            raise RuntimeError(f"Task {task_id} is already running.")
        try:
            yield
        finally:
            self.release_task_lock(task_id, token)
