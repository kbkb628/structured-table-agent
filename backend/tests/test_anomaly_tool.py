import json

from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.tools.anomaly_tool import anomaly_analysis


def test_anomaly_analysis_returns_only_outlier_rows(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount\n"
        "beauty,10000\n"
        "apparel,1000\n"
        "electronics,1000\n"
        "office,1000\n"
        "home,1000\n"
        "food,1000\n",
        encoding="utf-8",
    )

    save_file_record(
        FileRecord(
            file_id="file_anomaly_tool",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=6,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "product_category", "type": "string", "missing_rate": 0.0, "sample_values": [], "unique_count": 6},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 2},
                ]
            ),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    result = anomaly_analysis(
        file_id="file_anomaly_tool",
        group_by="product_category",
        metric_column="sales_amount",
        aggregation="sum",
        sort_order="desc",
        limit=10,
    )

    assert result.success is True
    assert len(result.data["rows"]) == 1
    assert result.data["rows"][0]["product_category"] == "beauty"
    assert result.data["rows"][0]["is_anomaly"] is True
    assert result.data["rows"][0]["z_score"] > 2
