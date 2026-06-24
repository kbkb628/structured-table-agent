import json
import time

import duckdb

from app.schemas.tool_schema import ToolError, ToolResponse
from app.storage.file_store import get_file_record


ALLOWED_AGGREGATIONS = {"sum", "avg", "count", "min", "max"}
ALLOWED_SORT_ORDERS = {"asc", "desc"}


def groupby_aggregate(
    file_id: str,
    group_by: str,
    metric_column: str,
    aggregation: str,
    sort_order: str,
    limit: int = 10,
) -> ToolResponse:
    started = time.perf_counter()
    if aggregation not in ALLOWED_AGGREGATIONS:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="INVALID_AGGREGATION",
                message=f"Unsupported aggregation: {aggregation}",
                suggested_fields=[],
            ),
            metadata={"elapsed_ms": 0},
        )
    if sort_order not in ALLOWED_SORT_ORDERS:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="INVALID_SORT_ORDER",
                message=f"Unsupported sort_order: {sort_order}",
                suggested_fields=[],
            ),
            metadata={"elapsed_ms": 0},
        )

    record = get_file_record(file_id)
    if record is None:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="FILE_NOT_FOUND",
                message=f"File {file_id} was not found",
                suggested_fields=[],
            ),
            metadata={"elapsed_ms": 0},
        )

    columns = {item["name"]: item for item in json.loads(record.columns_json)}
    if group_by not in columns:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="FIELD_NOT_FOUND",
                message=f"Field {group_by} was not found",
                suggested_fields=list(columns.keys()),
            ),
            metadata={"elapsed_ms": 0},
        )
    if metric_column not in columns:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="FIELD_NOT_FOUND",
                message=f"Field {metric_column} was not found",
                suggested_fields=list(columns.keys()),
            ),
            metadata={"elapsed_ms": 0},
        )
    if columns[metric_column]["type"] != "number" and aggregation in {"sum", "avg", "min", "max"}:
        return ToolResponse(
            success=False,
            tool_name="groupby_aggregate",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="NON_NUMERIC_METRIC",
                message=f"Field {metric_column} must be numeric for {aggregation}",
                suggested_fields=[],
            ),
            metadata={"elapsed_ms": 0},
        )

    sql = f"""
        SELECT "{group_by}" AS "{group_by}", {aggregation}("{metric_column}") AS "{metric_column}_{aggregation}"
        FROM read_csv_auto(?)
        GROUP BY 1
        ORDER BY 2 {sort_order.upper()}
        LIMIT ?
    """
    rows = duckdb.execute(sql, [record.stored_path, limit]).fetchdf().to_dict(orient="records")
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ToolResponse(
        success=True,
        tool_name="groupby_aggregate",
        data={"rows": rows},
        summary="aggregate rows grouped by the requested dimension",
        error=None,
        metadata={
            "columns_used": [group_by, metric_column],
            "row_count": len(rows),
            "elapsed_ms": elapsed_ms,
        },
    )
