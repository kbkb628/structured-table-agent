def match_fields(question: str, file_profile: dict) -> dict:
    lowered = question.lower()
    column_names = [column["name"] for column in file_profile["columns"]]

    def pick_dimension() -> str | None:
        keyword_pairs = [
            ("category", "product_category"),
            ("region", "region"),
            ("channel", "channel"),
        ]
        for keyword, field_name in keyword_pairs:
            if keyword in lowered and field_name in column_names:
                return field_name
        return None

    def pick_metric() -> tuple[str | None, str]:
        if "order" in lowered and "count" in lowered:
            return ("order_id" if "order_id" in column_names else None, "count")
        if "sales" in lowered and "sales_amount" in column_names:
            return ("sales_amount", "sum")
        return (None, "sum")

    dimension_field = pick_dimension()
    metric_field, aggregation = pick_metric()

    return {
        "dimension_field": dimension_field,
        "metric_field": metric_field,
        "aggregation": aggregation,
        "candidate_fields": column_names,
    }
