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
    assert "provider_smoke_error_message" in content
    assert "fixed_eval_average_trace_completeness" in content


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
    assert "provider_smoke_error_message" in content
    assert "fixed_eval_average_trace_completeness" in content


def test_root_readme_matches_current_runtime_truth():
    content = (Path(__file__).resolve().parents[2] / "README.md").read_text(
        encoding="utf-8"
    )

    assert "真实 Tongyi Qianwen Provider" in content or "真实通义千问 Provider" in content
    assert "GET /api/project-status" in content
    assert "demo_mvp.ps1" in content
    assert "未实现真实 LLM Provider" not in content
    assert "provider_smoke_error_message" in content
    assert "fixed_eval_average_report_completeness" in content


def test_architecture_overview_mentions_runtime_overview_and_demo_layers():
    content = (Path(__file__).resolve().parents[2] / "docs" / "ARCHITECTURE_OVERVIEW.md").read_text(
        encoding="utf-8"
    )

    assert "QwenClient" in content
    assert "route_next_step" in content
    assert "/demo" in content
    assert "GET /api/project-status" in content
    assert "llm.py" in content
    assert "project_status.py" in content
    assert "provider smoke" in content or "provider_smoke_error_message" in content
    assert "fixed eval" in content or "fixed_eval_average_trace_completeness" in content


def test_interview_guide_mentions_demo_script_diagnostic_outputs():
    content = (Path(__file__).resolve().parents[2] / "docs" / "INTERVIEW_GUIDE.md").read_text(
        encoding="utf-8"
    )

    assert "demo_mvp.ps1" in content
    assert "provider smoke" in content or "provider smoke failed" in content or "provider 解析结果" in content
    assert "fixed eval" in content or "质量指标" in content
