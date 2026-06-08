from fastapi.testclient import TestClient

from app.main import app


def test_upload_csv_returns_profile(tmp_path):
    client = TestClient(app)
    response = client.post(
        "/api/files/upload",
        files={"file": ("sales_orders.csv", "product_category,sales_amount\nelectronics,1000\n", "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "sales_orders.csv"
    assert body["row_count"] == 1
    assert body["column_count"] == 2
    assert body["columns"][0]["name"] == "product_category"


def test_get_profile_returns_persisted_profile():
    client = TestClient(app)
    upload_response = client.post(
        "/api/files/upload",
        files={"file": ("sales_orders.csv", "product_category,sales_amount\nelectronics,1000\n", "text/csv")},
    )
    file_id = upload_response.json()["file_id"]

    profile_response = client.get(f"/api/files/{file_id}/profile")

    assert profile_response.status_code == 200
    assert profile_response.json()["file_id"] == file_id
