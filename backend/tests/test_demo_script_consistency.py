from pathlib import Path


def test_demo_script_questions_match_readme_demo_questions():
    repo_root = Path(__file__).resolve().parents[2]
    readme = (repo_root / "backend" / "README.md").read_text(encoding="utf-8")
    script = (repo_root / "scripts" / "demo_mvp.ps1").read_text(encoding="utf-8")

    expected_questions = [
        "analyse category sales top 5",
        "analyse category sales share",
        "analyse category sales anomalies",
        "analyse sales by region",
        "analyse sales trend by order date",
        "analyse channel order count and sales performance",
    ]

    for question in expected_questions:
        assert f"- `{question}`" in readme
        assert f'"{question}"' in script


def test_demo_script_mentions_project_status_summary_output():
    repo_root = Path(__file__).resolve().parents[2]
    script = (repo_root / "scripts" / "demo_mvp.ps1").read_text(encoding="utf-8")

    assert "/api/project-status" in script
    assert "project_status_provider" in script
    assert "project_status_demo_available" in script


def test_demo_script_mentions_provider_and_eval_summary_output():
    repo_root = Path(__file__).resolve().parents[2]
    script = (repo_root / "scripts" / "demo_mvp.ps1").read_text(encoding="utf-8")

    assert "/api/llm/provider-status" in script
    assert "/api/llm/provider-smoke" in script
    assert "/api/eval/cases/run" in script
    assert "provider_status_key_source" in script
    assert "provider_smoke_ok" in script
    assert "fixed_eval_pass_rate" in script
