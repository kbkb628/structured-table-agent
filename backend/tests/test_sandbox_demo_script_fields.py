import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_demo_contract() -> dict:
    return json.loads(
        (_repo_root() / "scripts" / "demo_mvp_contract.json").read_text(encoding="utf-8")
    )


def _read_demo_script() -> str:
    return (_repo_root() / "scripts" / "demo_mvp.ps1").read_text(encoding="utf-8")


def test_demo_script_freezes_sandbox_runtime_fields():
    script = _read_demo_script()

    assert "project_status_sandbox_enabled" in script
    assert "project_status_sandbox_docker_available" in script
    assert "project_status_sandbox_supported_templates" in script
    assert "project_status_sandbox_max_timeout_seconds" in script
    assert "project_status_sandbox_max_code_chars" in script
    assert "project_status_sandbox_latest_execution_mode" in script
    assert "project_status_sandbox_latest_template_name" in script
    assert "project_status_sandbox_latest_python_code_char_count" in script
    assert "project_status_sandbox_latest_parsed_output_keys" in script
    assert "project_status_sandbox_latest_template_result_field_count" in script
    assert "project_status_sandbox_latest_error_code" in script


def test_demo_contract_freezes_sandbox_runtime_fields():
    contract = _load_demo_contract()
    top_level_fields = contract["top_level_fields"][0]
    documented_summary_fields = contract["documented_summary_fields"]

    assert "project_status_sandbox_enabled" in top_level_fields
    assert "project_status_sandbox_docker_available" in top_level_fields
    assert "project_status_sandbox_supported_templates" in top_level_fields
    assert "project_status_sandbox_max_timeout_seconds" in top_level_fields
    assert "project_status_sandbox_max_code_chars" in top_level_fields
    assert "project_status_sandbox_latest_execution_mode" in top_level_fields
    assert "project_status_sandbox_latest_template_name" in top_level_fields
    assert "project_status_sandbox_latest_python_code_char_count" in top_level_fields
    assert "project_status_sandbox_latest_parsed_output_keys" in top_level_fields
    assert "project_status_sandbox_latest_template_result_field_count" in top_level_fields
    assert "project_status_sandbox_latest_error_code" in top_level_fields

    assert "project_status_sandbox_enabled" in documented_summary_fields
    assert "project_status_sandbox_docker_available" in documented_summary_fields
    assert "project_status_sandbox_supported_templates" in documented_summary_fields
    assert "project_status_sandbox_max_timeout_seconds" in documented_summary_fields
    assert "project_status_sandbox_max_code_chars" in documented_summary_fields
    assert "project_status_sandbox_latest_execution_mode" in documented_summary_fields
    assert "project_status_sandbox_latest_template_name" in documented_summary_fields
    assert "project_status_sandbox_latest_python_code_char_count" in documented_summary_fields
    assert "project_status_sandbox_latest_parsed_output_keys" in documented_summary_fields
    assert "project_status_sandbox_latest_template_result_field_count" in documented_summary_fields
    assert "project_status_sandbox_latest_error_code" in documented_summary_fields


def test_delivery_docs_freeze_demo_script_sandbox_field_names():
    repo_root = _repo_root()
    root_readme = (repo_root / "README.md").read_text(encoding="utf-8")
    backend_readme = (repo_root / "backend" / "README.md").read_text(encoding="utf-8")
    api_reference = (repo_root / "docs" / "API_REFERENCE.md").read_text(encoding="utf-8")
    project_status = (repo_root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    interview_guide = (repo_root / "docs" / "INTERVIEW_GUIDE.md").read_text(encoding="utf-8")
    resume_description = (repo_root / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(
        encoding="utf-8"
    )
    evidence_map = (repo_root / "docs" / "RESUME_EVIDENCE_MAP.md").read_text(encoding="utf-8")

    common_fields = [
        "project_status_sandbox_enabled",
        "project_status_sandbox_docker_available",
        "project_status_sandbox_supported_templates",
        "project_status_sandbox_max_timeout_seconds",
        "project_status_sandbox_max_code_chars",
        "project_status_sandbox_latest_execution_mode",
        "project_status_sandbox_latest_template_name",
        "project_status_sandbox_latest_python_code_char_count",
        "project_status_sandbox_latest_parsed_output_keys",
        "project_status_sandbox_latest_template_result_field_count",
        "project_status_sandbox_latest_error_code",
    ]

    for field in common_fields:
        assert field in root_readme
        assert field in backend_readme
        assert field in api_reference
        assert field in project_status
        assert field in interview_guide

    assert "project_status_sandbox_latest_template_name" in resume_description
    assert "project_status_sandbox_latest_python_code_char_count" in evidence_map
