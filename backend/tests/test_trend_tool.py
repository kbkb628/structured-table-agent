import json

from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.tools.trend_tool import trend_analysis


def test_trend_analysis_returns_rows_sorted_by_order_date(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "order_date,sales_amount\n"
        "2026-06-03,800\n"
        "2026-06-01,1200\n"
        "2026-06-02,500\n"
        "2026-06-01,300\n",
        encoding="utf-8",
    )

    save_file_record(
        FileRecord(
            file_id="file_trend_tool",
            filename="sales_orders.csv",
            stored_path=str(csv_path),
            row_count=4,
            column_count=2,
            columns_json=json.dumps(
                [
                    {"name": "order_date", "type": "date", "missing_rate": 0.0, "sample_values": [], "unique_count": 3},
                    {"name": "sales_amount", "type": "number", "missing_rate": 0.0, "sample_values": [], "unique_count": 4},
                ]
            ),
            created_at="2026-06-17T00:00:00+00:00",
        )
    )

    result = trend_analysis(
        file_id="file_trend_tool",
        group_by="order_date",
        metric_column="sales_amount",
        aggregation="sum",
        sort_order="asc",
        limit=10,
    )

    assert result.success is True
    assert [row["order_date"] for row in result.data["rows"]] == [
        "2026-06-01",
        "2026-06-02",
        "2026-06-03",
    ]
    assert result.data["rows"][0]["sales_amount_sum"] == 1500
    assert result.metadata["trend_axis"] == "order_date"
