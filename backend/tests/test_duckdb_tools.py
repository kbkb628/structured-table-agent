import json
from pathlib import Path

from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.tools.duckdb_tools import groupby_aggregate


def test_groupby_aggregate_returns_top5(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "electronics,1200\n"
        "office,800\n"
        "electronics,500\n",
        encoding="utf-8",
    )

    save_file_record(
        FileRecord(
            file_id="file_agg",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=2,
            columns_json=json.dumps(
                [
                    {
                        "name": "product_category",
                        "type": "string",
                        "missing_rate": 0.0,
                        "sample_values": [],
                        "unique_count": 2,
                    },
                    {
                        "name": "sales_amount",
                        "type": "number",
                        "missing_rate": 0.0,
                        "sample_values": [],
                        "unique_count": 3,
                    },
                ],
                ensure_ascii=False,
            ),
            created_at="2026-06-08T18:00:00",
        )
    )

    result = groupby_aggregate(
        file_id="file_agg",
        group_by="product_category",
        metric_column="sales_amount",
        aggregation="sum",
        sort_order="desc",
        limit=5,
    )

    assert result.success is True
    assert result.data["rows"][0]["product_category"] == "electronics"
    assert result.data["rows"][0]["sales_amount_sum"] == 1700


def test_groupby_aggregate_rejects_non_numeric_metric(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "channel,order_id\n"
        "Online,ORD1\n"
        "Retail,ORD2\n",
        encoding="utf-8",
    )

    save_file_record(
        FileRecord(
            file_id="file_bad_metric",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=2,
            column_count=2,
            columns_json=json.dumps(
                [
                    {
                        "name": "channel",
                        "type": "string",
                        "missing_rate": 0.0,
                        "sample_values": [],
                        "unique_count": 2,
                    },
                    {
                        "name": "order_id",
                        "type": "string",
                        "missing_rate": 0.0,
                        "sample_values": [],
                        "unique_count": 2,
                    },
                ],
                ensure_ascii=False,
            ),
            created_at="2026-06-08T18:00:00",
        )
    )

    result = groupby_aggregate(
        file_id="file_bad_metric",
        group_by="channel",
        metric_column="order_id",
        aggregation="sum",
        sort_order="desc",
        limit=5,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "NON_NUMERIC_METRIC"
