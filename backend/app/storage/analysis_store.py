import json
import uuid
from datetime import datetime, timezone

from app.storage.database import get_connection, init_db


def _ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_task(task_id: str, file_id: str, question: str, state: dict) -> None:
    init_db()
    now = _ts()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO analysis_tasks (
                task_id, file_id, question, status, state_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, file_id, question, state["status"], json.dumps(state, ensure_ascii=False), now, now),
        )


def update_task_state(task_id: str, state: dict) -> None:
    init_db()
    now = _ts()
    with get_connection() as conn:
        updated = conn.execute(
            """
            UPDATE analysis_tasks
            SET status = ?, state_json = ?, updated_at = ?
            WHERE task_id = ?
            """,
            (state["status"], json.dumps(state, ensure_ascii=False), now, task_id),
        )
        if updated.rowcount == 0:
            conn.execute(
                """
                INSERT OR REPLACE INTO analysis_tasks (
                    task_id, file_id, question, status, state_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    state["file_id"],
                    state["question"],
                    state["status"],
                    json.dumps(state, ensure_ascii=False),
                    now,
                    now,
                ),
            )


def get_task_state(task_id: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT state_json FROM analysis_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()

    return json.loads(row[0]) if row else None


def record_event(task_id: str, event_type: str, node: str, message: str, payload: dict) -> dict:
    init_db()
    event = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "node": node,
        "message": message,
        "payload": payload,
        "created_at": _ts(),
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analysis_events (event_id, task_id, event_type, node, message, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                task_id,
                event["event_type"],
                event["node"],
                event["message"],
                json.dumps(event["payload"], ensure_ascii=False),
                event["created_at"],
            ),
        )

    return event


def list_task_events(task_id: str) -> list[dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT event_id, event_type, node, message, payload_json, created_at
            FROM analysis_events
            WHERE task_id = ?
            ORDER BY created_at ASC
            """,
            (task_id,),
        ).fetchall()

    return [
        {
            "event_id": row[0],
            "event_type": row[1],
            "node": row[2],
            "message": row[3],
            "payload": json.loads(row[4]),
            "created_at": row[5],
        }
        for row in rows
    ]


def record_tool_call(task_id: str, tool_name: str, request: dict, response: dict) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO tool_call_logs (log_id, task_id, tool_name, request_json, response_json, success, elapsed_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"log_{uuid.uuid4().hex[:12]}",
                task_id,
                tool_name,
                json.dumps(request, ensure_ascii=False),
                json.dumps(response, ensure_ascii=False),
                1 if response.get("success") else 0,
                int(response.get("metadata", {}).get("elapsed_ms", 0)),
                _ts(),
            ),
        )


def get_tool_call_logs(task_id: str) -> list[dict]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT log_id, task_id, tool_name, request_json, response_json, success, elapsed_ms, created_at
            FROM tool_call_logs
            WHERE task_id = ?
            ORDER BY created_at ASC
            """,
            (task_id,),
        ).fetchall()

    return [
        {
            "log_id": row[0],
            "task_id": row[1],
            "tool_name": row[2],
            "request_json": row[3],
            "response_json": row[4],
            "success": bool(row[5]),
            "elapsed_ms": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]


def record_eval_result(task_id: str, eval_result: dict) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO eval_results (eval_id, task_id, score_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                f"eval_{uuid.uuid4().hex[:12]}",
                task_id,
                json.dumps(eval_result, ensure_ascii=False),
                _ts(),
            ),
        )
