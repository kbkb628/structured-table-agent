from pathlib import Path


def test_interview_guide_describes_redis_as_degradable_not_absent():
    content = (Path(__file__).resolve().parents[2] / "docs" / "INTERVIEW_GUIDE.md").read_text(
        encoding="utf-8"
    )

    assert "当前没有 Redis" not in content
    assert "Redis" in content


def test_api_reference_mentions_demo_route_and_current_eval_case_count():
    content = (Path(__file__).resolve().parents[2] / "docs" / "API_REFERENCE.md").read_text(
        encoding="utf-8"
    )

    assert "GET /demo" in content
    assert "GET /api/project-status" in content
    assert "当前 6 个真实支持 case" in content
