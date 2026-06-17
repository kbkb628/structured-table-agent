from app.eval.eval_cases import get_fixed_eval_cases, run_fixed_eval_cases


def test_get_fixed_eval_cases_returns_three_supported_cases():
    cases = get_fixed_eval_cases()

    assert len(cases) == 3
    assert {case["case_id"] for case in cases} == {"category_topn", "region_compare", "channel_performance"}


def test_run_fixed_eval_cases_returns_passing_summary():
    summary = run_fixed_eval_cases()

    assert summary["total_cases"] == 3
    assert summary["passed_cases"] == 3
    assert summary["failed_cases"] == 0
    assert summary["pass_rate"] == 1.0
    assert len(summary["results"]) == 3
    assert all(item["passed"] is True for item in summary["results"])
    assert all(item["overall_score"] >= 0.8 for item in summary["results"])
    assert all(item["issues"] == [] for item in summary["results"])
    assert all(item["assertion_failures"] == [] for item in summary["results"])
