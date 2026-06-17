import json
from io import BytesIO
from pathlib import Path

import pandas as pd
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
from app.tools.registry import invoke_tool

router = APIRouter(prefix="/api/files", tags=["files"])
SUPPORTED_UPLOAD_SUFFIXES = {".csv", ".xlsx", ".xls"}


def _normalise_uploaded_content(filename: str, content: bytes) -> tuple[str, bytes]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return filename, content

    try:
        dataframe = pd.read_excel(BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {exc}") from exc

    normalised_name = f"{Path(filename).stem}.csv"
    return normalised_name, dataframe.to_csv(index=False).encode("utf-8")


@router.post("/upload", response_model=FileProfile)
async def upload_file(file: UploadFile = File(...)) -> FileProfile:
    if not file.filename or Path(file.filename).suffix.lower() not in SUPPORTED_UPLOAD_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    normalised_filename, normalised_content = _normalise_uploaded_content(file.filename, content)
    file_id = make_file_id()
    stored_name = f"{file_id}_{normalised_filename}"
    full_path = persist_uploaded_file(stored_name, normalised_content)
    created_at = make_timestamp()
    profile_result = invoke_tool(
        "profile_dataset",
        csv_path=full_path,
        file_id=file_id,
        created_at=created_at,
        filename=file.filename,
    )
    if not profile_result.success or profile_result.data is None:
        raise HTTPException(status_code=500, detail="Failed to build file profile.")
    profile = FileProfile.model_validate(profile_result.data)

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
