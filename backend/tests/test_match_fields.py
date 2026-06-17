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
