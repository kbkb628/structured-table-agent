from pathlib import Path


def test_interview_guide_describes_redis_as_degradable_not_absent():
    content = (Path(__file__).resolve().parents[2] / "docs" / "INTERVIEW_GUIDE.md").read_text(
        encoding="utf-8"
    )

    assert "当前没有 Redis" not in content
    assert "Redis" in content
    assert "GET /api/project-status" in content
    assert "/demo" in content


def test_api_reference_mentions_demo_route_and_current_eval_case_count():
    content = (Path(__file__).resolve().parents[2] / "docs" / "API_REFERENCE.md").read_text(
        encoding="utf-8"
    )

    assert "GET /demo" in content
    assert "GET /api/project-status" in content
    assert "当前 6 个真实支持 case" in content


def test_resume_project_description_mentions_qwen_and_project_status_delivery():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(
        encoding="utf-8"
    )

    assert "Tongyi Qianwen" in content or "通义千问" in content
    assert "project-status" in content
    assert "demo_mvp.ps1" in content


def test_project_status_mentions_project_overview_and_latest_smoke_evidence():
    content = (Path(__file__).resolve().parents[2] / "docs" / "PROJECT_STATUS.md").read_text(
        encoding="utf-8"
    )

    assert "GET /api/project-status" in content
    assert "GET /demo" in content
    assert "OPENAI_API_KEY_0011AI" in content
    assert "401 invalid_api_key" in content
