from app.tools.registry import invoke_tool


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
