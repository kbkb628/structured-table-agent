from app.schemas.judge_schema import JudgeResult


def test_judge_result_requires_dimensions_and_summary():
    result = JudgeResult.model_validate(
        {
            "judge_summary": "Report is well grounded in tool evidence.",
            "judge_status": "ok",
            "dimensions": {
                "groundedness": {"score": 0.95, "verdict": "supported", "rationale": "Tool rows support the key findings."},
                "completeness": {"score": 0.9, "verdict": "complete", "rationale": "Required report sections are present."},
                "clarity": {"score": 0.88, "verdict": "clear", "rationale": "The report is understandable."},
            },
            "issue_count": 0,
            "issues": [],
            "degraded": False,
        }
    )

    assert result.judge_status == "ok"
    assert result.dimensions["groundedness"].score == 0.95
