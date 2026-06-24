import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import UPLOAD_DIR
from app.storage.database import get_connection, init_db
from app.storage.models import FileRecord


def persist_uploaded_file(filename: str, content: bytes) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_DIR / filename
    stored_path.write_bytes(content)
    return stored_path


def make_file_id() -> str:
    return f"file_{uuid.uuid4().hex[:12]}"


def make_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def save_file_record(record: FileRecord) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO files (
                file_id, filename, stored_path, row_count, column_count, columns_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.file_id,
                record.filename,
                record.stored_path,
                record.row_count,
                record.column_count,
                record.columns_json,
                record.created_at,
            ),
        )


def get_file_record(file_id: str) -> FileRecord | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT file_id, filename, stored_path, row_count, column_count, columns_json, created_at
            FROM files
            WHERE file_id = ?
            """,
            (file_id,),
        ).fetchone()

    return FileRecord(*row) if row else None
