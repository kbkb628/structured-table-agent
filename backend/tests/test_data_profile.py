from pathlib import Path

from app.tools.data_profile import build_file_profile
from app.tools.data_profile import profile_dataset


def test_build_file_profile_returns_expected_shape(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount,order_status\n"
        "electronics,1200,completed\n"
        "office,800,cancelled\n",
        encoding="utf-8",
    )

    profile = build_file_profile(csv_path)

    assert profile.row_count == 2
    assert profile.column_count == 3
    assert profile.columns[0].name == "product_category"
    assert profile.columns[1].type == "number"


def test_profile_dataset_returns_tool_response(tmp_path: Path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount,order_status\n"
        "electronics,1200,completed\n"
        "office,800,cancelled\n",
        encoding="utf-8",
    )

    result = profile_dataset(csv_path, file_id="file_profile_tool", created_at="2026-06-17T00:00:00+00:00")

    assert result.success is True
    assert result.tool_name == "profile_dataset"
    assert result.data["row_count"] == 2
    assert result.data["column_count"] == 3
