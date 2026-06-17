from app.eval.eval_cases import _register_sample_file, get_fixed_eval_cases, run_fixed_eval_cases


def test_get_fixed_eval_cases_returns_three_supported_cases():
    cases = get_fixed_eval_cases()

    assert len(cases) == 3
    assert {case["case_id"] for case in cases} == {"category_topn", "region_compare", "channel_performance"}


def test_run_fixed_eval_cases_returns_passing_summary():
    summary = run_fixed_eval_cases()

    assert summary["total_cases"] == 3
    assert summary["passed_cases"] == 3
    assert summary["failed_cases"] == 0
    assert summary["pass_rate"] == 1.0
    assert len(summary["results"]) == 3
    assert all(item["passed"] is True for item in summary["results"])
    assert all(item["overall_score"] >= 0.8 for item in summary["results"])
    assert all(item["issues"] == [] for item in summary["results"])
    assert all(item["assertion_failures"] == [] for item in summary["results"])


def test_register_sample_file_uses_profile_dataset_tool(monkeypatch):
    captured: dict = {}

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
                "row_count": 3,
                "column_count": 2,
                "columns": [
                    {
                        "name": "region",
                        "type": "string",
                        "missing_rate": 0.0,
                        "sample_values": ["East"],
                        "unique_count": 1,
                    }
                ],
                "created_at": kwargs["created_at"],
            },
            summary="ok",
            error=None,
            metadata={"row_count": 3, "column_count": 2},
        )

    import app.eval.eval_cases as eval_cases

    assert hasattr(eval_cases, "invoke_tool")
    assert not hasattr(eval_cases, "build_file_profile")
    monkeypatch.setattr("app.eval.eval_cases.invoke_tool", fake_invoke_tool, raising=False)

    profile = _register_sample_file()

    assert captured["tool_name"] == "profile_dataset"
    assert profile["file_id"] == captured["kwargs"]["file_id"]
    assert profile["filename"] == "sales_orders.csv"
