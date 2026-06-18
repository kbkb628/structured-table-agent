import json
import logging
import threading
import time
import uuid
from contextlib import contextmanager

from app.observability.event_logger import record_analysis_event
from app.observability.event_logger import record_session_state_recovered
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
            "final_report": f"final_report:{task_id}",
            "llm_judgement": f"llm_judgement:{task_id}",
            "intermediate_findings": f"intermediate_findings:{task_id}",
            "business_context": f"business_context:{task_id}",
            "latest_context": f"latest_context:{task_id}",
            "task_lock": f"task_lock:{task_id}",
        }

    def _build_context_checkpoint(self, state: dict) -> dict:
        business_context = state.get("business_context", []) or []
        intermediate_findings = state.get("intermediate_findings", []) or []
        draft_report = state.get("draft_report", {}) or {}
        latest_error = (state.get("errors") or [])[-1] if state.get("errors") else {}
        checkpoint = {
            "analysis_goal": state.get("analysis_goal", ""),
            "current_step": state.get("current_step", ""),
            "status": state.get("status", ""),
            "pending_metric_count": len(state.get("pending_metrics", []) or []),
            "finding_count": len(intermediate_findings),
            "business_context_titles": [item.get("title") for item in business_context if item.get("title")],
            "draft_report_status": "available" if draft_report else "empty",
            "latest_error_code": latest_error.get("code", ""),
        }
        return checkpoint

    def _record_context_checkpoint_refreshed(self, task_id: str, checkpoint: dict) -> None:
        record_analysis_event(
            task_id,
            "context_checkpoint_refreshed",
            "session_store",
            "context checkpoint refreshed",
            checkpoint,
        )

    def _record_session_state_recovered(self, task_id: str, recovered_segments: list[str]) -> None:
        record_session_state_recovered(
            task_id,
            {
                "recovery_source": "sqlite_plus_granular_redis",
                "recovered_segments": recovered_segments,
            },
        )

    def _connect(self):
        if redis is None:
            return None
        try:
            client = redis.Redis.from_url(self._url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    def _hydrate_state_from_granular_keys(
        self,
        client,
        task_id: str,
        base_state: dict | None = None,
    ) -> tuple[dict | None, list[str]]:
        keys = self._build_keys(task_id)
        state = dict(base_state) if base_state is not None else None

        granular_payloads = {
            "draft_report": client.get(keys["draft_report"]),
            "final_report": client.get(keys["final_report"]),
            "llm_judgement": client.get(keys["llm_judgement"]),
            "intermediate_findings": client.get(keys["intermediate_findings"]),
            "business_context": client.get(keys["business_context"]),
            "context_checkpoint": client.get(keys["latest_context"]),
        }
        recovered_segments = [name for name, payload in granular_payloads.items() if payload]
        if not recovered_segments:
            return None, []

        if state is None:
            state = get_task_state(task_id)
            if state is None:
                return None, []

        if granular_payloads["draft_report"]:
            state["draft_report"] = json.loads(granular_payloads["draft_report"])
        if granular_payloads["final_report"]:
            state["final_report"] = json.loads(granular_payloads["final_report"])
        if granular_payloads["llm_judgement"]:
            state["llm_judgement"] = json.loads(granular_payloads["llm_judgement"])
        if granular_payloads["intermediate_findings"]:
            state["intermediate_findings"] = json.loads(granular_payloads["intermediate_findings"])
        if granular_payloads["business_context"]:
            state["business_context"] = json.loads(granular_payloads["business_context"])
        if granular_payloads["context_checkpoint"]:
            state["context_checkpoint"] = json.loads(granular_payloads["context_checkpoint"])
        else:
            state["context_checkpoint"] = self._build_context_checkpoint(state)
        return state, recovered_segments

    def load_state(self, task_id: str) -> tuple[dict | None, bool]:
        client = self._connect()
        if client is not None:
            payload = client.get(self._build_keys(task_id)["analysis_state"])
            if payload:
                state = json.loads(payload)
                hydrated_state, _ = self._hydrate_state_from_granular_keys(client, task_id, base_state=state)
                return hydrated_state or state, True

            hydrated_state, recovered_segments = self._hydrate_state_from_granular_keys(client, task_id)
            if hydrated_state is not None:
                logger.warning(
                    "Redis analysis_state missing; rebuilding task %s from SQLite state plus granular Redis keys",
                    task_id,
                )
                client.set(
                    self._build_keys(task_id)["analysis_state"],
                    json.dumps(hydrated_state, ensure_ascii=False),
                )
                update_task_state(task_id, hydrated_state)
                self._record_session_state_recovered(task_id, recovered_segments)
                return hydrated_state, True
        logger.warning("Redis unavailable; falling back to SQLite-backed session state for task %s", task_id)
        state = get_task_state(task_id)
        if state is not None and "context_checkpoint" not in state:
            state["context_checkpoint"] = self._build_context_checkpoint(state)
        return state, False

    def save_state(self, task_id: str, state: dict) -> bool:
        client = self._connect()
        context_checkpoint = self._build_context_checkpoint(state)
        state["context_checkpoint"] = context_checkpoint
        if client is not None:
            keys = self._build_keys(task_id)
            client.set(keys["analysis_state"], json.dumps(state, ensure_ascii=False))
            client.set(keys["draft_report"], json.dumps(state.get("draft_report", {}), ensure_ascii=False))
            client.set(keys["final_report"], json.dumps(state.get("final_report", {}), ensure_ascii=False))
            client.set(keys["llm_judgement"], json.dumps(state.get("llm_judgement", {}), ensure_ascii=False))
            client.set(
                keys["intermediate_findings"],
                json.dumps(state.get("intermediate_findings", []), ensure_ascii=False),
            )
            client.set(
                keys["business_context"],
                json.dumps(state.get("business_context", []), ensure_ascii=False),
            )
            client.set(keys["latest_context"], json.dumps(context_checkpoint, ensure_ascii=False))
            self._record_context_checkpoint_refreshed(task_id, context_checkpoint)
            update_task_state(task_id, state)
            return True
        logger.warning("Redis unavailable; persisting session state to SQLite for task %s", task_id)
        self._record_context_checkpoint_refreshed(task_id, context_checkpoint)
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
