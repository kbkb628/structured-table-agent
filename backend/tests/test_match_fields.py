from app.tools.match_fields import match_fields


def test_match_fields_detects_region_sales_question():
    file_profile = {
        "columns": [
            {"name": "region", "type": "string"},
            {"name": "sales_amount", "type": "number"},
            {"name": "channel", "type": "string"},
        ]
    }

    result = match_fields("analyse sales by region", file_profile)

    assert result.success is True
    assert result.data["dimension_field"] == "region"
    assert result.data["metric_field"] == "sales_amount"
    assert result.data["aggregation"] == "sum"
    assert result.data["planned_tool_sequence"] == ["groupby_aggregate", "generate_chart", "generate_report"]
    assert result.data["planned_tool_calls"][0]["tool_name"] == "groupby_aggregate"
    assert result.data["planned_tool_calls"][0]["group_by"] == "region"


def test_match_fields_builds_channel_dual_metric_plan():
    file_profile = {
        "columns": [
            {"name": "channel", "type": "string"},
            {"name": "order_id", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    result = match_fields("analyse channel order count and sales performance", file_profile)

    assert result.success is True
    assert result.data["analysis_type"] == "channel_performance"
    assert result.data["dimension_field"] == "channel"
    assert len(result.data["metrics"]) == 2
    assert result.data["metrics"][0] == {
        "metric_field": "order_id",
        "aggregation": "count",
        "label": "order_count",
    }
    assert result.data["metrics"][1] == {
        "metric_field": "sales_amount",
        "aggregation": "sum",
        "label": "sales_amount_sum",
    }
    assert [item["tool_name"] for item in result.data["planned_tool_calls"]] == [
        "groupby_aggregate",
        "groupby_aggregate",
    ]
    assert result.data["planned_tool_calls"][0]["label"] == "order_count"
    assert result.data["planned_tool_calls"][1]["label"] == "sales_amount_sum"


def test_match_fields_routes_share_question_to_calculate_share():
    file_profile = {
        "columns": [
            {"name": "product_category", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    result = match_fields("analyse category sales share", file_profile)

    assert result.success is True
    assert result.data["analysis_type"] == "share_analysis"
    assert result.data["planned_tool_calls"][0]["tool_name"] == "calculate_share"
    assert result.data["planned_tool_sequence"][0] == "calculate_share"


def test_match_fields_routes_trend_question_to_trend_analysis():
    file_profile = {
        "columns": [
            {"name": "order_date", "type": "date"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    result = match_fields("analyse sales trend by order date", file_profile)

    assert result.success is True
    assert result.data["analysis_type"] == "trend_analysis"
    assert result.data["dimension_field"] == "order_date"
    assert result.data["planned_tool_calls"][0]["tool_name"] == "trend_analysis"
    assert result.data["planned_tool_calls"][0]["sort_order"] == "asc"


def test_match_fields_routes_anomaly_question_to_anomaly_analysis():
    file_profile = {
        "columns": [
            {"name": "product_category", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    result = match_fields("analyse category sales anomalies", file_profile)

    assert result.success is True
    assert result.data["analysis_type"] == "anomaly_analysis"
    assert result.data["dimension_field"] == "product_category"
    assert result.data["planned_tool_calls"][0]["tool_name"] == "anomaly_analysis"
