import json
import uuid
from datetime import datetime, timezone

from app.storage.database import get_connection
from app.storage.database import init_db


def _ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _summarize_request_payload(request_payload: dict) -> dict:
    python_code = request_payload.get("python_code") or ""
    template_name = request_payload.get("template_name")
    return {
        "execution_mode": "template" if template_name else "inline_python",
        "template_name": template_name,
        "python_code_char_count": len(python_code),
    }


def record_sandbox_execution(file_id: str, request_payload: dict, response_payload: dict, execution_source: str) -> str:
    init_db()
    execution_id = f"sandbox_exec_{uuid.uuid4().hex[:12]}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sandbox_execution_logs (
                execution_id, file_id, execution_source, request_json, response_json, success, elapsed_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                file_id,
                execution_source,
                json.dumps(request_payload, ensure_ascii=False),
                json.dumps(response_payload, ensure_ascii=False),
                1 if response_payload.get("status") == "completed" else 0,
                int(response_payload.get("elapsed_ms", 0) or 0),
                _ts(),
            ),
        )
    return execution_id


def get_latest_sandbox_execution() -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT execution_id, file_id, execution_source, request_json, response_json, success, elapsed_ms, created_at
            FROM sandbox_execution_logs
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    request_payload = json.loads(row[3]) if row[3] else {}
    response_payload = json.loads(row[4]) if row[4] else {}
    return {
        "execution_id": row[0],
        "file_id": row[1],
        "execution_source": row[2],
        "success": bool(row[5]),
        "elapsed_ms": int(row[6] or 0),
        "created_at": row[7],
        **_summarize_request_payload(request_payload),
        **response_payload,
    }
