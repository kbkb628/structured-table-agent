from app.eval.rule_scorer import score_task_state


def test_score_task_state_returns_high_score_for_complete_task():
    state = {
        "field_understanding": {"dimension_field": "region", "metric_field": "sales_amount"},
        "tool_results": [
            {
                "success": True,
                "tool_name": "groupby_aggregate",
                "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
                "metadata": {"elapsed_ms": 12},
            }
        ],
        "chart_specs": [{"chart_type": "bar", "plotly_spec": {"data": [{"type": "bar"}]}}],
        "final_report": {
            "title": "Analysis Report: analyse sales by region",
            "analysis_goal": "compare region sales",
            "key_findings": [{"finding": "East performs best", "evidence": "1200", "source_tool": "groupby_aggregate"}],
            "chart_explanations": ["Bar chart generated for bar view."],
            "business_suggestions": ["Focus on East."],
            "data_limitations": ["Uploaded CSV only."],
            "next_steps": ["Check by channel."],
        },
        "events": [
            {"event_type": "task_created"},
            {"event_type": "fields_matched"},
            {"event_type": "tool_succeeded"},
            {"event_type": "chart_generated"},
            {"event_type": "report_generated"},
            {"event_type": "task_completed"},
        ],
        "status": "completed",
    }

    result = score_task_state(state)

    assert result["schema_valid"] is True
    assert result["tool_success_rate"] == 1.0
    assert result["tool_elapsed_ms_total"] == 12
    assert result["chart_validity"] is True
    assert result["report_completeness"] == 1.0
    assert result["trace_completeness"] == 1.0
    assert result["overall_score"] >= 0.9
    assert result["issues"] == []


def test_score_task_state_reports_missing_chart_and_trace():
    state = {
        "field_understanding": {"dimension_field": "region", "metric_field": "sales_amount"},
        "tool_results": [
            {
                "success": True,
                "tool_name": "groupby_aggregate",
                "data": {"rows": [{"region": "East", "sales_amount_sum": 1200}]},
                "metadata": {"elapsed_ms": 8},
            }
        ],
        "chart_specs": [],
        "final_report": {
            "title": "Analysis Report: analyse sales by region",
            "analysis_goal": "compare region sales",
            "key_findings": [{"finding": "East performs best", "evidence": "1200", "source_tool": "groupby_aggregate"}],
            "chart_explanations": [],
            "business_suggestions": ["Focus on East."],
            "data_limitations": ["Uploaded CSV only."],
            "next_steps": ["Check by channel."],
        },
        "events": [
            {"event_type": "task_created"},
            {"event_type": "fields_matched"},
            {"event_type": "tool_succeeded"},
        ],
        "status": "completed",
    }

    result = score_task_state(state)

    assert result["chart_validity"] is False
    assert result["tool_elapsed_ms_total"] == 8
    assert result["trace_completeness"] < 1.0
    assert any("chart" in issue.lower() for issue in result["issues"])
    assert any("trace" in suggestion.lower() for suggestion in result["suggestions"])
