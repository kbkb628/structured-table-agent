from pathlib import Path

from app.tools.data_profile import build_file_profile


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
