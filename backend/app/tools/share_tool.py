import json
import time

import duckdb

from app.schemas.tool_schema import ToolError, ToolResponse
from app.storage.file_store import get_file_record
from app.tools.duckdb_tools import ALLOWED_AGGREGATIONS, ALLOWED_SORT_ORDERS


def calculate_share(
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
            tool_name="calculate_share",
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
            tool_name="calculate_share",
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
            tool_name="calculate_share",
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
            tool_name="calculate_share",
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
            tool_name="calculate_share",
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
            tool_name="calculate_share",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="NON_NUMERIC_METRIC",
                message=f"Field {metric_column} must be numeric for {aggregation}",
                suggested_fields=[],
            ),
            metadata={"elapsed_ms": 0},
        )

    metric_label = f"{metric_column}_{aggregation}"
    sql = f"""
        WITH grouped AS (
            SELECT
                "{group_by}" AS "{group_by}",
                {aggregation}("{metric_column}") AS "{metric_label}"
            FROM read_csv_auto(?)
            GROUP BY 1
        ),
        total AS (
            SELECT SUM("{metric_label}") AS total_metric
            FROM grouped
        )
        SELECT
            g."{group_by}" AS "{group_by}",
            g."{metric_label}" AS "{metric_label}",
            CASE
                WHEN t.total_metric = 0 OR t.total_metric IS NULL THEN 0
                ELSE g."{metric_label}" * 1.0 / t.total_metric
            END AS share_ratio,
            CASE
                WHEN t.total_metric = 0 OR t.total_metric IS NULL THEN 0
                ELSE ROUND(g."{metric_label}" * 100.0 / t.total_metric, 2)
            END AS share_percent
        FROM grouped g
        CROSS JOIN total t
        ORDER BY share_ratio {sort_order.upper()}
        LIMIT ?
    """
    rows = duckdb.execute(sql, [record.stored_path, limit]).fetchdf().to_dict(orient="records")
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ToolResponse(
        success=True,
        tool_name="calculate_share",
        data={"rows": rows},
        summary="calculated grouped metric contribution share",
        error=None,
        metadata={
            "columns_used": [group_by, metric_column],
            "row_count": len(rows),
            "elapsed_ms": elapsed_ms,
        },
    )
