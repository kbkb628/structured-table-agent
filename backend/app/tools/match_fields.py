from app.schemas.tool_schema import ToolResponse


def _build_planned_tool_calls(dimension_field: str | None, metrics: list[dict[str, str]]) -> list[dict[str, str | int]]:
    if dimension_field is None:
        return []
    planned_calls: list[dict[str, str | int]] = []
    for metric in metrics:
        planned_calls.append(
            {
                "tool_name": "groupby_aggregate",
                "group_by": dimension_field,
                "metric_column": metric["metric_field"],
                "aggregation": metric["aggregation"],
                "sort_order": "desc",
                "limit": 5,
                "label": metric["label"],
            }
        )
    return planned_calls


def _build_trend_tool_call(dimension_field: str | None, metric: dict[str, str] | None) -> list[dict[str, str | int]]:
    if dimension_field is None or metric is None or metric.get("metric_field") is None:
        return []
    return [
        {
            "tool_name": "trend_analysis",
            "group_by": dimension_field,
            "metric_column": metric["metric_field"],
            "aggregation": metric["aggregation"],
            "sort_order": "asc",
            "limit": 31,
            "label": metric["label"],
        }
    ]


def _build_anomaly_tool_call(dimension_field: str | None, metric: dict[str, str] | None) -> list[dict[str, str | int]]:
    if dimension_field is None or metric is None or metric.get("metric_field") is None:
        return []
    return [
        {
            "tool_name": "anomaly_analysis",
            "group_by": dimension_field,
            "metric_column": metric["metric_field"],
            "aggregation": metric["aggregation"],
            "sort_order": "desc",
            "limit": 10,
            "label": metric["label"],
        }
    ]


def _build_share_tool_call(dimension_field: str | None, metric: dict[str, str] | None) -> list[dict[str, str | int]]:
    if dimension_field is None or metric is None or metric.get("metric_field") is None:
        return []
    return [
        {
            "tool_name": "calculate_share",
            "group_by": dimension_field,
            "metric_column": metric["metric_field"],
            "aggregation": metric["aggregation"],
            "sort_order": "desc",
            "limit": 5,
            "label": f"{metric['label']}_share",
        }
    ]


def match_fields(question: str, file_profile: dict) -> ToolResponse:
    lowered = question.lower()
    column_names = [column["name"] for column in file_profile["columns"]]

    def contains_any(*terms: str) -> bool:
        return any(term in question or term in lowered for term in terms)

    def pick_dimension() -> str | None:
        if contains_any("trend", "date", "time", "趋势", "日期", "时间") and "order_date" in column_names:
            return "order_date"
        keyword_pairs = [
            (("category", "品类", "类别"), "product_category"),
            (("region", "地区", "区域"), "region"),
            (("channel", "渠道"), "channel"),
        ]
        for keywords, field_name in keyword_pairs:
            if any(keyword in question or keyword in lowered for keyword in keywords) and field_name in column_names:
                return field_name
        return None

    def has_term(*terms: str) -> bool:
        return all(term in lowered for term in terms)

    dimension_field = pick_dimension()
    metrics: list[dict[str, str]] = []
    warnings: list[str] = []
    analysis_type = "single_metric"

    wants_order_count = has_term("order", "count") or contains_any("订单数", "订单量", "单量")
    wants_sales = contains_any("sales", "sale", "revenue", "gmv", "销售额", "销售金额", "金额", "成交额")
    wants_share = contains_any("share", "占比", "比例", "贡献")
    wants_trend = contains_any("trend", "趋势") or (contains_any("date", "日期", "时间") and wants_sales)
    wants_anomaly = contains_any("anomal", "outlier", "异常", "离群")

    if dimension_field == "channel" and wants_order_count and wants_sales:
        analysis_type = "channel_performance"
        if "order_id" in column_names:
            metrics.append(
                {
                    "metric_field": "order_id",
                    "aggregation": "count",
                    "label": "order_count",
                }
            )
        else:
            warnings.append("Missing order_id for order count analysis.")
        if "sales_amount" in column_names:
            metrics.append(
                {
                    "metric_field": "sales_amount",
                    "aggregation": "sum",
                    "label": "sales_amount_sum",
                }
            )
        else:
            warnings.append("Missing sales_amount for sales analysis.")
    elif wants_order_count:
        if "order_id" in column_names:
            metrics.append(
                {
                    "metric_field": "order_id",
                    "aggregation": "count",
                    "label": "order_count",
                }
            )
        else:
            warnings.append("Missing order_id for order count analysis.")
    elif wants_sales:
        if "sales_amount" in column_names:
            metrics.append(
                {
                    "metric_field": "sales_amount",
                    "aggregation": "sum",
                    "label": "sales_amount_sum",
                }
            )
        else:
            warnings.append("Missing sales_amount for sales analysis.")
    else:
        warnings.append("No supported metric intent was detected.")

    if dimension_field is None:
        warnings.append("No supported dimension field was matched.")

    primary_metric = metrics[0] if metrics else {"metric_field": None, "aggregation": "sum"}
    if wants_anomaly and metrics:
        analysis_type = "anomaly_analysis"
        planned_tool_calls = _build_anomaly_tool_call(dimension_field, primary_metric)
        planned_tool_sequence = ["anomaly_analysis", "generate_chart", "generate_report"]
    elif wants_trend and metrics and dimension_field == "order_date":
        analysis_type = "trend_analysis"
        planned_tool_calls = _build_trend_tool_call(dimension_field, primary_metric)
        planned_tool_sequence = ["trend_analysis", "generate_chart", "generate_report"]
    elif wants_share and metrics:
        analysis_type = "share_analysis"
        planned_tool_calls = _build_share_tool_call(dimension_field, primary_metric)
        planned_tool_sequence = ["calculate_share", "generate_chart", "generate_report"]
    else:
        planned_tool_calls = _build_planned_tool_calls(dimension_field, metrics)
        planned_tool_sequence = ["groupby_aggregate", "generate_chart", "generate_report"]

    return ToolResponse(
        success=True,
        tool_name="match_fields",
        data={
            "dimension_field": dimension_field,
            "metric_field": primary_metric["metric_field"],
            "aggregation": primary_metric["aggregation"],
            "analysis_type": analysis_type,
            "metrics": metrics,
            "planned_tool_calls": planned_tool_calls,
            "planned_tool_sequence": planned_tool_sequence,
            "candidate_fields": column_names,
            "warnings": warnings,
        },
        summary="matched candidate dimension and metric fields for the requested analysis",
        error=None,
        metadata={"column_count": len(column_names), "warning_count": len(warnings)},
    )
