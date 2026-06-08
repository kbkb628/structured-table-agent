def generate_chart(title: str, x_field: str, y_field: str, rows: list[dict]) -> dict:
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
            "layout": {"title": title},
        },
    }
