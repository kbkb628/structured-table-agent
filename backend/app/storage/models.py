from dataclasses import dataclass


@dataclass(slots=True)
class FileRecord:
    file_id: str
    filename: str
    stored_path: str
    row_count: int
    column_count: int
    columns_json: str
    created_at: str
