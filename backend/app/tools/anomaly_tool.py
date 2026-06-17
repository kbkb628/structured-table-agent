import json
import math
import time

import duckdb

from app.schemas.tool_schema import ToolError
from app.schemas.tool_schema import ToolResponse
from app.storage.file_store import get_file_record
from app.tools.duckdb_tools import ALLOWED_AGGREGATIONS
from app.tools.duckdb_tools import ALLOWED_SORT_ORDERS


def anomaly_analysis(
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
            tool_name="anomaly_analysis",
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
            tool_name="anomaly_analysis",
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
            tool_name="anomaly_analysis",
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
            tool_name="anomaly_analysis",
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
            tool_name="anomaly_analysis",
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
            tool_name="anomaly_analysis",
            data=None,
            summary="tool execution failed",
            error=ToolError(
                code="NON_NUMERIC_METRIC",
                message=f"Field {metric_column} must be numeric for {aggregation}",
                suggested_fields=[],
            ),
            metadata={"elapsed_ms": 0},
        )

    result_field = f"{metric_column}_{aggregation}"
    sql = f"""
        SELECT "{group_by}" AS "{group_by}", {aggregation}("{metric_column}") AS "{result_field}"
        FROM read_csv_auto(?)
        GROUP BY 1
    """
    rows = duckdb.execute(sql, [record.stored_path]).fetchdf().to_dict(orient="records")

    values = [float(row[result_field]) for row in rows]
    mean_value = sum(values) / len(values) if values else 0.0
    variance = sum((value - mean_value) ** 2 for value in values) / len(values) if values else 0.0
    stddev = math.sqrt(variance)

    anomaly_rows: list[dict] = []
    for row in rows:
        metric_value = float(row[result_field])
        z_score = 0.0 if stddev == 0 else (metric_value - mean_value) / stddev
        enriched_row = {
            **row,
            "z_score": round(z_score, 4),
            "is_anomaly": z_score >= 1.5,
        }
        if enriched_row["is_anomaly"]:
            anomaly_rows.append(enriched_row)

    anomaly_rows.sort(key=lambda item: item[result_field], reverse=(sort_order == "desc"))
    anomaly_rows = anomaly_rows[:limit]
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return ToolResponse(
        success=True,
        tool_name="anomaly_analysis",
        data={"rows": anomaly_rows},
        summary="detected grouped metric outliers using z-score over aggregated rows",
        error=None,
        metadata={
            "columns_used": [group_by, metric_column],
            "row_count": len(anomaly_rows),
            "elapsed_ms": elapsed_ms,
            "baseline_row_count": len(rows),
            "zscore_threshold": 1.5,
        },
    )
