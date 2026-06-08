from app.tools.chart_tool import generate_chart
from app.tools.report_tool import generate_report


def test_generate_chart_returns_bar_spec():
    rows = [
        {"region": "East", "sales_amount_sum": 1200},
        {"region": "West", "sales_amount_sum": 800},
    ]

    result = generate_chart(
        title="Sales by Region",
        x_field="region",
        y_field="sales_amount_sum",
        rows=rows,
    )

    assert result["chart_type"] == "bar"
    assert result["plotly_spec"]["data"][0]["type"] == "bar"


def test_generate_report_uses_tool_numbers():
    report = generate_report(
        question="analyse sales by region",
        analysis_goal="compare region sales",
        tool_result={
            "tool_name": "groupby_aggregate",
            "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
        },
        chart_spec={"chart_type": "bar"},
    )

    assert report["analysis_goal"] == "compare region sales"
    assert report["key_findings"][0]["source_tool"] == "groupby_aggregate"
    assert "1200" in report["key_findings"][0]["evidence"]
