from app.schemas.tool_schema import ToolError, ToolResponse
from app.tools.registry import invoke_tool, invoke_tool_with_retry


def test_invoke_match_fields_returns_tool_response():
    result = invoke_tool(
        "match_fields",
        question="analyse sales by region",
        file_profile={
            "columns": [
                {"name": "region", "type": "string"},
                {"name": "sales_amount", "type": "number"},
                {"name": "channel", "type": "string"},
            ]
        },
    )

    assert result.success is True
    assert result.tool_name == "match_fields"
    assert result.data["dimension_field"] == "region"
    assert result.data["metric_field"] == "sales_amount"


def test_invoke_generate_chart_returns_tool_response():
    result = invoke_tool(
        "generate_chart",
        title="Sales by Region",
        x_field="region",
        y_field="sales_amount_sum",
        rows=[
            {"region": "East", "sales_amount_sum": 1200},
            {"region": "West", "sales_amount_sum": 800},
        ],
    )

    assert result.success is True
    assert result.tool_name == "generate_chart"
    assert result.data["chart_type"] == "bar"
    assert result.data["plotly_spec"]["data"][0]["type"] == "bar"


def test_invoke_generate_chart_returns_failure_response_for_empty_rows():
    result = invoke_tool(
        "generate_chart",
        title="Sales by Region",
        x_field="region",
        y_field="sales_amount_sum",
        rows=[],
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "CHART_GENERATION_FAILED"


def test_invoke_generate_report_returns_tool_response():
    result = invoke_tool(
        "generate_report",
        question="analyse sales by region",
        analysis_goal="compare region sales",
        tool_results=[
            {
                "tool_name": "groupby_aggregate",
                "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
            }
        ],
        chart_specs=[{"chart_type": "bar"}],
    )

    assert result.success is True
    assert result.tool_name == "generate_report"
    assert result.data["analysis_goal"] == "compare region sales"
    assert result.data["key_findings"][0]["source_tool"] == "groupby_aggregate"


def test_invoke_profile_dataset_returns_tool_response(tmp_path):
    csv_path = tmp_path / "sales_orders.csv"
    csv_path.write_text(
        "product_category,sales_amount,order_status\n"
        "electronics,1200,completed\n"
        "office,800,cancelled\n",
        encoding="utf-8",
    )

    result = invoke_tool(
        "profile_dataset",
        csv_path=csv_path,
        file_id="file_profile_tool",
        created_at="2026-06-17T00:00:00+00:00",
    )

    assert result.success is True
    assert result.tool_name == "profile_dataset"
    assert result.data["row_count"] == 2
    assert result.data["column_count"] == 3


def test_invoke_tool_with_retry_retries_once_and_marks_metadata(monkeypatch):
    calls = {"count": 0}

    def flaky_tool(**kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return ToolResponse(
                success=False,
                tool_name="flaky_tool",
                data=None,
                summary="tool execution failed",
                error=ToolError(code="TEMP_ERROR", message="temporary failure", suggested_fields=[]),
                metadata={},
            )
        return ToolResponse(
            success=True,
            tool_name="flaky_tool",
            data={"rows": [{"region": "East", "sales_amount_sum": 1200}]},
            summary="retry succeeded",
            error=None,
            metadata={},
        )

    monkeypatch.setattr(
        "app.tools.registry.get_tool_registry",
        lambda: {"flaky_tool": flaky_tool},
    )

    result = invoke_tool_with_retry("flaky_tool", max_retries=1, group_by="region")

    assert result.success is True
    assert calls["count"] == 2
    assert result.metadata["retry_attempts"] == 1
    assert result.metadata["retry_status"] == "recovered"


def test_invoke_tool_with_retry_returns_failure_after_retry_exhausted(monkeypatch):
    calls = {"count": 0}

    def always_fail(**kwargs):
        calls["count"] += 1
        return ToolResponse(
            success=False,
            tool_name="always_fail",
            data=None,
            summary="tool execution failed",
            error=ToolError(code="TEMP_ERROR", message="temporary failure", suggested_fields=[]),
            metadata={},
        )

    monkeypatch.setattr(
        "app.tools.registry.get_tool_registry",
        lambda: {"always_fail": always_fail},
    )

    result = invoke_tool_with_retry("always_fail", max_retries=1, group_by="region")

    assert result.success is False
    assert calls["count"] == 2
    assert result.metadata["retry_attempts"] == 1
    assert result.metadata["retry_status"] == "exhausted"


def test_invoke_tool_returns_schema_failure_for_missing_required_parameter():
    result = invoke_tool(
        "generate_chart",
        title="Sales by Region",
        x_field="region",
        rows=[{"region": "East", "sales_amount_sum": 1200}],
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "TOOL_ARGUMENT_VALIDATION_FAILED"
    assert "y_field" in result.error.message


def test_invoke_tool_returns_schema_failure_for_invalid_parameter_type():
    result = invoke_tool(
        "groupby_aggregate",
        file_id="file_missing",
        group_by="region",
        metric_column="sales_amount",
        aggregation="sum",
        sort_order="desc",
        limit="five",
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "TOOL_ARGUMENT_VALIDATION_FAILED"
    assert "limit" in result.error.message


def test_invoke_tool_returns_failure_for_invalid_tool_response(monkeypatch):
    def invalid_tool(**kwargs):
        return {
            "success": True,
            "tool_name": "invalid_tool",
            "data": {"rows": []},
            "summary": "broken response",
            "metadata": "not-a-dict",
        }

    monkeypatch.setattr(
        "app.tools.registry.get_tool_registry",
        lambda: {"invalid_tool": invalid_tool},
    )

    result = invoke_tool("invalid_tool", anything="value")

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "TOOL_RESPONSE_VALIDATION_FAILED"
    assert "metadata" in result.error.message


def test_invoke_tool_returns_failure_for_invalid_tool_output_data(monkeypatch):
    def invalid_chart_tool(**kwargs):
        return ToolResponse(
            success=True,
            tool_name="generate_chart",
            data={
                "chart_type": "bar",
                "plotly_spec": {
                    "data": "not-a-list",
                    "layout": {"title": "Sales by Region"},
                },
            },
            summary="broken chart output",
            error=None,
            metadata={},
        )

    monkeypatch.setattr(
        "app.tools.registry.get_tool_registry",
        lambda: {"generate_chart": invalid_chart_tool},
    )

    result = invoke_tool(
        "generate_chart",
        title="Sales by Region",
        x_field="region",
        y_field="sales_amount_sum",
        rows=[{"region": "East", "sales_amount_sum": 1200}],
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "TOOL_DATA_VALIDATION_FAILED"
    assert "plotly_spec" in result.error.message
