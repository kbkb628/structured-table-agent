from pathlib import Path

import pandas as pd

from app.schemas.file_schema import ColumnProfile, FileProfile
from app.schemas.tool_schema import ToolResponse


def _map_dtype(dtype: str) -> str:
    if "int" in dtype or "float" in dtype:
        return "number"
    return "string"


def build_file_profile(
    csv_path: Path,
    file_id: str = "",
    created_at: str = "",
    filename: str | None = None,
) -> FileProfile:
    df = pd.read_csv(csv_path)
    columns: list[ColumnProfile] = []
    for column_name in df.columns:
        series = df[column_name]
        samples = [str(value) for value in series.dropna().head(3).tolist()]
        columns.append(
            ColumnProfile(
                name=column_name,
                type=_map_dtype(str(series.dtype)),
                missing_rate=round(float(series.isna().mean()), 4),
                sample_values=samples,
                unique_count=int(series.nunique(dropna=True)),
            )
        )

    return FileProfile(
        file_id=file_id,
        filename=filename or csv_path.name,
        row_count=int(len(df)),
        column_count=int(len(df.columns)),
        columns=columns,
        created_at=created_at,
    )


def profile_dataset(
    csv_path: Path,
    file_id: str = "",
    created_at: str = "",
    filename: str | None = None,
) -> ToolResponse:
    profile = build_file_profile(
        csv_path=csv_path,
        file_id=file_id,
        created_at=created_at,
        filename=filename,
    )
    return ToolResponse(
        success=True,
        tool_name="profile_dataset",
        data=profile.model_dump(),
        summary="built a dataset profile from the uploaded CSV",
        error=None,
        metadata={"row_count": profile.row_count, "column_count": profile.column_count},
    )
