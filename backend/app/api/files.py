import json

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.file_schema import FileProfile
from app.storage.file_store import (
    get_file_record,
    make_file_id,
    make_timestamp,
    persist_uploaded_file,
    save_file_record,
)
from app.storage.models import FileRecord
from app.tools.data_profile import build_file_profile

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload", response_model=FileProfile)
async def upload_file(file: UploadFile = File(...)) -> FileProfile:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_id = make_file_id()
    stored_name = f"{file_id}_{file.filename}"
    full_path = persist_uploaded_file(stored_name, content)
    created_at = make_timestamp()
    profile = build_file_profile(
        full_path,
        file_id=file_id,
        created_at=created_at,
        filename=file.filename,
    )

    save_file_record(
        FileRecord(
            file_id=profile.file_id,
            filename=profile.filename,
            stored_path=str(full_path),
            row_count=profile.row_count,
            column_count=profile.column_count,
            columns_json=json.dumps([item.model_dump() for item in profile.columns], ensure_ascii=False),
            created_at=profile.created_at,
        )
    )
    return profile


@router.get("/{file_id}/profile", response_model=FileProfile)
def get_profile(file_id: str) -> FileProfile:
    record = get_file_record(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="File profile not found.")

    return FileProfile(
        file_id=record.file_id,
        filename=record.filename,
        row_count=record.row_count,
        column_count=record.column_count,
        columns=json.loads(record.columns_json),
        created_at=record.created_at,
    )
