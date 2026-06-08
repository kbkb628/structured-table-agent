from pydantic import BaseModel


class ColumnProfile(BaseModel):
    name: str
    type: str
    missing_rate: float
    sample_values: list[str]
    unique_count: int


class FileProfile(BaseModel):
    file_id: str
    filename: str
    row_count: int
    column_count: int
    columns: list[ColumnProfile]
    created_at: str
