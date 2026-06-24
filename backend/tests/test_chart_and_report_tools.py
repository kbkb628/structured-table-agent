from app.tools.chart_tool import generate_chart
from app.tools.report_tool import generate_report
from app.schemas.report_schema import FinalReport


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

    assert result.success is True
    assert result.data["chart_type"] == "bar"
    assert result.data["plotly_spec"]["data"][0]["type"] == "bar"
    assert result.data["plotly_spec"]["layout"]["title"] == "Sales by Region"
    assert result.data["plotly_spec"]["layout"]["xaxis"]["title"] == "region"
    assert result.data["plotly_spec"]["layout"]["yaxis"]["title"] == "sales_amount_sum"
    assert result.data["figure_backend"] == "plotly"
    assert result.data["plotly_trace_count"] == 1


def test_generate_chart_supports_line_spec():
    rows = [
        {"order_date": "2026-06-01", "sales_amount_sum": 1200},
        {"order_date": "2026-06-02", "sales_amount_sum": 1500},
    ]

    result = generate_chart(
        title="Sales Trend",
        x_field="order_date",
        y_field="sales_amount_sum",
        rows=rows,
        chart_type="line",
    )

    assert result.success is True
    assert result.data["chart_type"] == "line"
    assert result.data["plotly_spec"]["data"][0]["type"] == "scatter"
    assert result.data["plotly_spec"]["data"][0]["mode"] == "lines+markers"
    assert result.data["figure_backend"] == "plotly"
    assert result.data["plotly_trace_count"] == 1


def test_generate_chart_rejects_empty_rows():
    result = generate_chart(
        title="Sales by Region",
        x_field="region",
        y_field="sales_amount_sum",
        rows=[],
    )

    assert result.success is False
    assert result.error is not None
    assert "Rows cannot be empty" in result.error.message


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

    assert report.success is True
    assert report.data["analysis_goal"] == "compare region sales"
    assert report.data["key_findings"][0]["source_tool"] == "groupby_aggregate"
    assert "1200" in report.data["key_findings"][0]["evidence"]


def test_generate_report_falls_back_when_no_tool_rows():
    report = generate_report(
        question="analyse sales by region",
        analysis_goal="compare region sales",
        tool_results=[],
        chart_specs=[],
    )

    assert report.success is True
    assert report.data["key_findings"][0]["source_tool"] == "report_builder"
    assert report.data["chart_explanations"][0] == "No chart was generated; conclusions are based on tabular tool results."


def test_generate_report_returns_final_report_schema():
    report = generate_report(
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

    validated = FinalReport.model_validate(report.data)

    assert validated.analysis_goal == "compare region sales"
    assert validated.key_findings[0].source_tool == "groupby_aggregate"


def test_generate_report_uses_chart_type_specific_explanation():
    report = generate_report(
        question="analyse sales trend by order date",
        analysis_goal="analyse sales trend over time",
        tool_results=[
            {
                "tool_name": "trend_analysis",
                "data": {"rows": [{"order_date": "2026-06-01", "sales_amount_sum": 1200}]},
            }
        ],
        chart_specs=[{"chart_type": "line"}],
    )

    assert report.success is True
    assert report.data["chart_explanations"][0] == "Line chart generated for line view."


def test_generate_report_uses_share_specific_key_finding():
    report = generate_report(
        question="analyse category sales share",
        analysis_goal="compare category sales share",
        tool_results=[
            {
                "tool_name": "calculate_share",
                "data": {
                    "rows": [
                        {
                            "product_category": "electronics",
                            "sales_amount_sum": 2200,
                            "share_ratio": 0.7333,
                            "share_percent": 73.33,
                        }
                    ]
                },
            }
        ],
        chart_specs=[{"chart_type": "bar"}],
    )

    assert report.success is True
    assert report.data["key_findings"][0]["finding"] == "electronics contributes the highest grouped share in the current result set"
    assert "share_percent = 73.33" in report.data["key_findings"][0]["evidence"]


def test_generate_report_uses_trend_specific_key_finding():
    report = generate_report(
        question="analyse sales trend by order date",
        analysis_goal="analyse sales trend over time",
        tool_results=[
            {
                "tool_name": "trend_analysis",
                "data": {
                    "rows": [
                        {"order_date": "2026-06-01", "sales_amount_sum": 1500},
                        {"order_date": "2026-06-03", "sales_amount_sum": 800},
                    ]
                },
            }
        ],
        chart_specs=[{"chart_type": "line"}],
    )

    assert report.success is True
    assert report.data["key_findings"][0]["finding"] == "sales_amount_sum changes over time across the available dates"
    assert "2026-06-01" in report.data["key_findings"][0]["evidence"]
    assert "2026-06-03" in report.data["key_findings"][0]["evidence"]


def test_generate_report_uses_anomaly_specific_key_finding():
    report = generate_report(
        question="analyse category sales anomalies",
        analysis_goal="detect abnormal category sales",
        tool_results=[
            {
                "tool_name": "anomaly_analysis",
                "data": {
                    "rows": [
                        {
                            "product_category": "beauty",
                            "sales_amount_sum": 10000,
                            "z_score": 2.2361,
                            "is_anomaly": True,
                        }
                    ]
                },
            }
        ],
        chart_specs=[{"chart_type": "bar"}],
    )

    assert report.success is True
    assert report.data["key_findings"][0]["finding"] == "beauty is the most prominent anomaly in the current result set"
    assert "z_score = 2.2361" in report.data["key_findings"][0]["evidence"]
