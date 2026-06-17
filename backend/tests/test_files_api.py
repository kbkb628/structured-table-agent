from fastapi.testclient import TestClient

from app.main import app


def test_upload_csv_uses_profile_dataset_tool(monkeypatch):
    client = TestClient(app)
    captured: dict = {}

    def fail_build_file_profile(*args, **kwargs):
        raise AssertionError("upload_file should use invoke_tool('profile_dataset') instead of build_file_profile")

    def fake_invoke_tool(tool_name: str, **kwargs):
        from app.schemas.tool_schema import ToolResponse

        captured["tool_name"] = tool_name
        captured["kwargs"] = kwargs
        return ToolResponse(
            success=True,
            tool_name="profile_dataset",
            data={
                "file_id": kwargs["file_id"],
                "filename": kwargs["filename"],
                "row_count": 1,
                "column_count": 2,
                "columns": [
                    {
                        "name": "product_category",
                        "type": "string",
                        "missing_rate": 0.0,
                        "sample_values": ["electronics"],
                        "unique_count": 1,
                    },
                    {
                        "name": "sales_amount",
                        "type": "number",
                        "missing_rate": 0.0,
                        "sample_values": ["1000"],
                        "unique_count": 1,
                    },
                ],
                "created_at": kwargs["created_at"],
            },
            summary="ok",
            error=None,
            metadata={"row_count": 1, "column_count": 2},
        )

    import app.api.files as files_api

    assert hasattr(files_api, "invoke_tool")
    assert not hasattr(files_api, "build_file_profile")
    monkeypatch.setattr("app.api.files.invoke_tool", fake_invoke_tool, raising=False)

    response = client.post(
        "/api/files/upload",
        files={"file": ("sales_orders.csv", "product_category,sales_amount\nelectronics,1000\n", "text/csv")},
    )

    assert response.status_code == 200
    assert captured["tool_name"] == "profile_dataset"
    assert captured["kwargs"]["filename"] == "sales_orders.csv"


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


def test_upload_rejects_non_csv_file():
    client = TestClient(app)

    response = client.post(
        "/api/files/upload",
        files={"file": ("sales_orders.txt", "not,a,csv\n", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported."


def test_upload_rejects_empty_file():
    client = TestClient(app)

    response = client.post(
        "/api/files/upload",
        files={"file": ("sales_orders.csv", "", "text/csv")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."
