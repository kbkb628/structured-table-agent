from app.storage.file_store import get_file_record, save_file_record
from app.storage.models import FileRecord


def test_file_record_roundtrip(tmp_path):
    record = FileRecord(
        file_id="file_test",
        filename="sales_orders.csv",
        stored_path=str(tmp_path / "sales_orders.csv"),
        row_count=3,
        column_count=2,
        columns_json="[]",
        created_at="2026-06-08T18:00:00",
    )

    save_file_record(record)
    loaded = get_file_record("file_test")

    assert loaded is not None
    assert loaded.file_id == "file_test"
    assert loaded.filename == "sales_orders.csv"
