import json
import re
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_demo_contract() -> dict:
    contract_path = _repo_root() / "scripts" / "demo_mvp_contract.json"
    return json.loads(contract_path.read_text(encoding="utf-8"))


def _read_demo_script() -> str:
    return (_repo_root() / "scripts" / "demo_mvp.ps1").read_text(encoding="utf-8")


def _extract_pscustomobject_fields(script: str) -> list[list[str]]:
    blocks = re.findall(r"\[pscustomobject\]@\{(.*?)\n\s*\}", script, flags=re.DOTALL)
    return [
        re.findall(r"^\s*([A-Za-z0-9_]+)\s*=", block, flags=re.MULTILINE)
        for block in blocks
    ]


def test_demo_script_questions_match_readme_demo_questions():
    repo_root = _repo_root()
    readme = (repo_root / "backend" / "README.md").read_text(encoding="utf-8")
    script = _read_demo_script()
    contract = _load_demo_contract()
    expected_questions = contract["questions"]

    for question in expected_questions:
        assert f"- `{question}`" in readme
        assert f'"{question}"' in script


def test_demo_script_mentions_project_status_summary_output():
    script = _read_demo_script()

    assert "/api/project-status" in script
    assert "project_status_provider" in script
    assert "project_status_demo_available" in script
    assert "project_status_session_store_active_backend" in script
    assert "project_status_session_store_redis_available" in script
    assert "project_status_session_store_degraded_to_sqlite" in script
    assert "project_status_session_store_warning_count" in script
    assert "project_status_session_store_recovered_count" in script
    assert "project_status_session_store_latest_recovered_recovery_source" in script
    assert "project_status_session_store_latest_recovered_segment_count" in script
    assert "project_status_session_store_latest_recovered_segments" in script
    assert "project_status_latest_task_has_business_context" in script
    assert "project_status_latest_task_has_llm_judgement" in script
    assert "project_status_latest_task_supported_by_tools" in script
    assert "project_status_latest_task_has_findings" in script
    assert "project_status_latest_task_tool_call_log_count" in script
    assert "project_status_latest_task_has_eval_result" in script
    assert "project_status_latest_task_eval_overall_score" in script
    assert "project_status_latest_task_eval_issue_count" in script
    assert "project_status_latest_task_pending_metric_count" in script
    assert "project_status_latest_task_planned_tool_call_count" in script
    assert "project_status_latest_task_event_count" in script
    assert "project_status_latest_task_latest_event_type" in script
    assert "project_status_latest_task_route_decision_count" in script
    assert "project_status_latest_task_continued_route_decision_count" in script
    assert "project_status_latest_task_finished_route_decision_count" in script
    assert "project_status_latest_task_latest_route_decision" in script
    assert "project_status_latest_task_chart_spec_count" in script
    assert "project_status_latest_task_key_finding_count" in script
    assert "project_status_latest_task_business_suggestion_count" in script
    assert "project_status_latest_task_data_limitation_count" in script
    assert "project_status_latest_task_business_context_count" in script
    assert "project_status_latest_task_top_business_context_title" in script
    assert "project_status_latest_task_top_business_context_score" in script
    assert "project_status_latest_task_top_business_context_related_field_count" in script
    assert "project_status_latest_task_top_business_context_has_score_breakdown" in script
    assert "project_status_latest_task_top_business_context_bm25_score" in script
    assert "project_status_latest_task_checkpoint_current_step" in script
    assert "project_status_latest_task_checkpoint_draft_report_status" in script
    assert "project_status_latest_task_analysis_goal" in script
    assert "project_status_latest_task_analysis_plan_count" in script
    assert "project_status_latest_task_completed_step_count" in script
    assert "project_status_latest_task_dimension_field" in script
    assert "project_status_latest_task_metric_count" in script
    assert "project_status_latest_task_match_analysis_type" in script
    assert "project_status_latest_task_candidate_field_count" in script
    assert "project_status_latest_task_match_warning_count" in script
    assert "project_status_latest_task_planned_tool_sequence" in script
    assert "project_status_latest_task_tool_result_count" in script
    assert "project_status_latest_task_successful_tool_result_count" in script
    assert "project_status_latest_task_failed_tool_result_count" in script
    assert "project_status_latest_task_total_tool_elapsed_ms" in script
    assert "project_status_latest_task_retried_tool_result_count" in script
    assert "project_status_latest_task_retry_attempts_total" in script
    assert "project_status_latest_task_latest_retry_status" in script
    assert "project_status_latest_task_error_count" in script
    assert "project_status_latest_task_latest_error_code" in script
    assert "project_status_latest_task_has_degradation" in script


def test_demo_script_mentions_provider_and_eval_summary_output():
    script = _read_demo_script()

    assert "/api/llm/provider-status" in script
    assert "/api/llm/provider-smoke" in script
    assert "/api/eval/cases/run" in script
    assert "provider_status_key_source" in script
    assert "provider_smoke_ok" in script
    assert "fixed_eval_pass_rate" in script
    assert "provider_smoke_error_type" in script
    assert "provider_smoke_error_message" in script
    assert "fixed_eval_average_trace_completeness" in script
    assert "fixed_eval_average_report_completeness" in script


def test_demo_script_contract_matches_pscustomobject_output_shape():
    contract = _load_demo_contract()
    object_fields = _extract_pscustomobject_fields(_read_demo_script())

    assert object_fields[0] == contract["run_fields"][0]
    assert object_fields[1] == contract["top_level_fields"][0]


def test_demo_script_contract_is_documented_across_delivery_docs():
    repo_root = _repo_root()
    contract = _load_demo_contract()
    root_readme = (repo_root / "README.md").read_text(encoding="utf-8")
    backend_readme = (repo_root / "backend" / "README.md").read_text(encoding="utf-8")
    api_reference = (repo_root / "docs" / "API_REFERENCE.md").read_text(encoding="utf-8")
    project_status = (repo_root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    interview_guide = (repo_root / "docs" / "INTERVIEW_GUIDE.md").read_text(encoding="utf-8")

    for field in contract["documented_summary_fields"]:
        assert field in root_readme
        assert field in backend_readme
        assert field in api_reference
        assert field in project_status
        assert field in interview_guide
