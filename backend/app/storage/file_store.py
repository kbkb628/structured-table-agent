from app.storage.database import get_connection, init_db
from app.storage.models import FileRecord


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
