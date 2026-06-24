import json

from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.tools.share_tool import calculate_share


def test_calculate_share_returns_share_ratio_and_percent(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "electronics,1200\n"
        "office,800\n"
        "electronics,1000\n",
        encoding="utf-8",
    )

    save_file_record(
        FileRecord(
            file_id="file_share_case",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=3,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
                ]
            ),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    result = calculate_share(
        file_id="file_share_case",
        group_by="product_category",
        metric_column="sales_amount",
        aggregation="sum",
        sort_order="desc",
        limit=5,
    )

    assert result.success is True
    assert result.data["rows"][0]["product_category"] == "electronics"
    assert result.data["rows"][0]["sales_amount_sum"] == 2200
    assert round(result.data["rows"][0]["share_ratio"], 2) == 0.73
    assert round(result.data["rows"][0]["share_percent"], 2) == 73.33


def test_calculate_share_rejects_missing_metric_field(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "electronics,1200\n",
        encoding="utf-8",
    )

    save_file_record(
        FileRecord(
            file_id="file_share_missing_metric",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=1,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 1},
                ]
            ),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    result = calculate_share(
        file_id="file_share_missing_metric",
        group_by="product_category",
        metric_column="missing_metric",
        aggregation="sum",
        sort_order="desc",
        limit=5,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "FIELD_NOT_FOUND"
