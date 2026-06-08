def generate_chart(title: str, x_field: str, y_field: str, rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("Rows cannot be empty for chart generation.")
    if x_field not in rows[0] or y_field not in rows[0]:
        raise ValueError(f"Chart fields {x_field} and {y_field} must exist in row data.")

    return {
        "chart_type": "bar",
        "plotly_spec": {
            "data": [
                {
                    "type": "bar",
                    "x": [row[x_field] for row in rows],
                    "y": [row[y_field] for row in rows],
                }
            ],
            "layout": {"title": title, "xaxis": {"title": x_field}, "yaxis": {"title": y_field}},
        },
    }
