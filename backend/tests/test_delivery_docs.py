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
    assert "summary.session_store" in content or "session store" in content
    assert "当前 9 个真实支持 case" in content
    assert "provider_smoke_error_message" in content
    assert "project_status_latest_task_has_context_checkpoint" in content
    assert "project_status_latest_task_eval_has_dimension_scores" in content
    assert "project_status_latest_task_latest_event_at" in content
    assert "project_status_latest_task_llm_issue_count" in content
    assert "project_status_latest_task_next_step_count" in content
    assert "project_status_latest_task_checkpoint_latest_error_code" in content
    assert "project_status_latest_task_current_step" in content
    assert "project_status_latest_task_finding_count" in content
    assert "project_status_latest_task_latest_finding_summary" in content
    assert "project_status_latest_task_latest_tool_name" in content
    assert "project_status_latest_task_top_key_finding" in content
    assert "project_status_latest_task_latest_error_message" in content
    assert "project_status_demo_available" in content
    assert "project_status_session_store_preferred_backend" in content
    assert "project_status_session_store_redis_available" in content
    assert "project_status_session_store_degraded_to_sqlite" in content
    assert "project_status_session_store_redis_url" in content
    assert "project_status_session_store_recovered_count" in content
    assert "project_status_session_store_latest_warning_task_id" in content
    assert "project_status_session_store_latest_warning_at" in content
    assert "project_status_session_store_latest_recovered_task_id" in content
    assert "project_status_session_store_latest_recovered_at" in content
    assert "project_status_latest_task_has_llm_judgement" in content
    assert "project_status_latest_task_judgement_issue_count" in content
    assert "project_status_latest_task_tool_call_log_count" in content
    assert "project_status_latest_task_eval_issue_count" in content
    assert "project_status_latest_task_planned_tool_call_count" in content
    assert "project_status_latest_task_event_count" in content
    assert "project_status_latest_task_business_suggestion_count" in content
    assert "project_status_latest_task_data_limitation_count" in content
    assert "project_status_latest_task_top_business_context_title" in content
    assert "project_status_latest_task_checkpoint_draft_report_status" in content
    assert "project_status_latest_task_completed_step_count" in content
    assert "project_status_latest_task_metric_count" in content
    assert "project_status_latest_task_successful_tool_result_count" in content
    assert "project_status_latest_task_failed_tool_result_count" in content
    assert "project_status_latest_task_latest_retry_status" in content
    assert "project_status_latest_task_latest_error_code" in content
    assert "project_status_files" in content
    assert "project_status_tasks" in content
    assert "project_status_analysis_events" in content
    assert "project_status_tool_call_logs" in content
    assert "project_status_eval_results" in content
    assert "project_status_files_exists" in content
    assert "project_status_tasks_exists" in content
    assert "project_status_analysis_events_exists" in content
    assert "project_status_tool_call_logs_exists" in content
    assert "project_status_eval_results_exists" in content
    assert "provider_status_allow_fallback" in content
    assert "provider_status_has_api_key" in content
    assert "provider_status_key_source" in content
    assert "provider_status_base_url" in content
    assert "provider_status_model" in content
    assert "provider_status_timeout_seconds" in content
    assert "provider_status_provider_supported" in content
    assert "provider_status_key_source_kind" in content
    assert "provider_status_smoke_ready" in content
    assert "provider_status_warnings" in content
    assert "provider_status_recommendations" in content
    assert "provider_smoke_ok" in content
    assert "provider_smoke_client_type" in content
    assert "provider_smoke_error_type" in content
    assert "fixed_eval_average_trace_completeness" in content
    assert "fixed_eval_average_tool_elapsed_ms_total" in content
    assert "fixed_eval_average_chart_validity" in content
    assert "fixed_eval_average_field_validity" in content
    assert "fixed_eval_pass_rate" in content
    assert "fixed_eval_passed_cases" in content
    assert "fixed_eval_total_cases" in content
    assert "fixed_eval_average_tool_success_rate" in content


def test_backend_readme_mentions_current_fixed_eval_scope():
    content = (Path(__file__).resolve().parents[2] / "backend" / "README.md").read_text(
        encoding="utf-8"
    )

    assert "nine fixed eval cases" in content
    assert "three Chinese MVP acceptance questions" in content


def test_demo_script_docs_describe_post_run_project_status_refresh():
    repo_root = Path(__file__).resolve().parents[2]
    root_readme = (repo_root / "README.md").read_text(encoding="utf-8")
    backend_readme = (repo_root / "backend" / "README.md").read_text(encoding="utf-8")

    assert "刷新 `GET /api/project-status`" in root_readme
    assert "refreshes `GET /api/project-status` after the demo runs" in backend_readme


def test_resume_project_description_mentions_qwen_and_project_status_delivery():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(
        encoding="utf-8"
    )

    assert "RESUME_EVIDENCE_MAP.md" in content
    assert "Tongyi Qianwen" in content or "通义千问" in content
    assert "project-status" in content
    assert "demo_mvp.ps1" in content
    assert "CSV / Excel" in content
    assert "route_next_step" in content
    assert "ToolResponse" in content
    assert "Pydantic schema" in content
    assert "z-score" in content
    assert "QwenClient" in content
    assert "MockLLMClient" in content
    assert "缺少可用 API key 时的显式降级" in content
    assert "llm_judgement" in content
    assert "BM25" in content
    assert "embedding" in content
    assert "rerank" in content
    assert "context_checkpoint" in content
    assert "真实 Plotly 图表生成" in content
    assert "plotly_spec" in content
    assert "Plotly 受控分析工具" not in content
    assert "SQLite 降级" in content or "SQLite" in content


def test_resume_evidence_map_links_resume_claims_to_runtime_evidence():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RESUME_EVIDENCE_MAP.md").read_text(
        encoding="utf-8"
    )

    assert "INTERVIEW_DEMO_CHECKLIST.md" in content
    assert "简历说法" in content
    assert "代码证据" in content
    assert "演示证据" in content
    assert "CSV / Excel" in content
    assert "route_next_step" in content
    assert "ToolResponse" in content
    assert "真实 Plotly 图表生成" in content
    assert "plotly_spec" in content
    assert "z-score" in content
    assert "QwenClient" in content
    assert "MockLLMClient" in content
    assert "缺少可用 API key 时" in content
    assert "llm_judgement" in content
    assert "score_breakdown" in content
    assert "embedding_score" in content or "top_business_context_embedding_score" in content
    assert "rerank_score" in content or "top_business_context_rerank_score" in content
    assert "retrieval_sources" in content
    assert "context_checkpoint" in content
    assert "analysis_state" in content
    assert "细粒度 Redis key" in content
    assert "provider-status" in content
    assert "provider-smoke" in content
    assert "project-status" in content
    assert "DockerSandbox" in content
    assert "advanced_code_execution" in content
    assert "demo_mvp.ps1" in content
    assert "test_files_api.py" in content
    assert "test_analysis_runner.py" in content
    assert "test_session_store.py" in content
    assert "test_keyword_retriever.py" in content
    assert "不能说已经实现 DockerSandbox" not in content
    assert "不能说 DockerSandbox 已经替代 DuckDB + 受控工具链成为默认分析路径" in content


def test_interview_demo_checklist_provides_short_demo_path():
    content = (Path(__file__).resolve().parents[2] / "docs" / "INTERVIEW_DEMO_CHECKLIST.md").read_text(
        encoding="utf-8"
    )

    assert "INTERVIEW_DEMO_PREFLIGHT.md" in content
    assert "最短演示路径" in content
    assert "/demo" in content
    assert "/api/llm/provider-status" in content
    assert "/api/llm/provider-smoke" in content
    assert "/api/project-status" in content
    assert "demo_mvp.ps1" in content
    assert "project_status_latest_task_analysis_goal" in content
    assert "project_status_latest_task_latest_route_decision" in content
    assert "project_status_latest_task_top_business_context_bm25_score" in content
    assert "project_status_latest_task_top_business_context_embedding_score" in content
    assert "project_status_latest_task_top_business_context_rerank_score" in content
    assert "project_status_latest_task_checkpoint_status" in content
    assert "fixed_eval_pass_rate" in content
    assert "不要说已经实现 DockerSandbox" not in content
    assert "不要说 DockerSandbox 是默认分析执行路径或已经替代主分析链" in content


def test_interview_demo_preflight_checklist_covers_startup_and_failure_checks():
    content = (Path(__file__).resolve().parents[2] / "docs" / "INTERVIEW_DEMO_PREFLIGHT.md").read_text(
        encoding="utf-8"
    )

    assert "RELEASE_READINESS_AUDIT.md" in content
    assert "演示前检查单" in content
    assert "uvicorn app.main:app" in content
    assert "/api/llm/provider-status" in content
    assert "/api/llm/provider-smoke" in content
    assert "/demo" in content
    assert "/api/project-status" in content
    assert "demo_mvp.ps1" in content
    assert "预期现象" in content
    assert "失败排查" in content
    assert "fixed_eval_pass_rate" in content


def test_release_readiness_audit_summarizes_ship_blockers_and_verification():
    content = (Path(__file__).resolve().parents[2] / "docs" / "RELEASE_READINESS_AUDIT.md").read_text(
        encoding="utf-8"
    )

    assert "可封板状态审计" in content
    assert "已具备" in content
    assert "仍未实现" in content
    assert "建议封板前确认" in content
    assert "uvicorn app.main:app" in content
    assert "pytest -q" in content
    assert "/api/project-status" in content
    assert "demo_mvp.ps1" in content
    assert "DockerSandbox" in content
    assert "advanced_code_execution" in content
    assert "如果目标是继续补 DockerSandbox" not in content
    assert "已实现但仍属第二阶段增强能力" in content


def test_project_status_mentions_project_overview_and_latest_smoke_evidence():
    content = (Path(__file__).resolve().parents[2] / "docs" / "PROJECT_STATUS.md").read_text(
        encoding="utf-8"
    )

    assert "GET /api/project-status" in content
    assert "GET /api/sandbox/status" in content
    assert "POST /api/sandbox/execute" in content
    assert "advanced_code_execution" in content
    assert "supported_templates" in content
    assert "max_code_chars" in content
    assert "execution_mode" in content
    assert "template_result_summary" in content
    assert "SANDBOX_NETWORK_ERROR" in content
    assert "summary.session_store" in content or "session store" in content
    assert "GET /demo" in content
    assert "plotly_spec" in content
    assert "真实 Plotly" in content
    assert "Plotly 的受控工具链" not in content
    assert "TONGYI_API_KEY" in content or "OPENAI_API_KEY_0011AI" in content
    assert "provider smoke returned `ok = true`" in content or "401 invalid_api_key" in content
    assert "provider_smoke_error_message" in content
    assert "project_status_latest_task_has_context_checkpoint" in content
    assert "project_status_latest_task_eval_has_dimension_scores" in content
    assert "project_status_latest_task_latest_event_at" in content
    assert "project_status_latest_task_llm_issue_count" in content
    assert "project_status_latest_task_next_step_count" in content
    assert "project_status_latest_task_checkpoint_latest_error_code" in content
    assert "project_status_latest_task_current_step" in content
    assert "project_status_latest_task_finding_count" in content
    assert "project_status_latest_task_latest_finding_summary" in content
    assert "project_status_latest_task_latest_tool_name" in content
    assert "project_status_latest_task_top_key_finding" in content
    assert "project_status_latest_task_latest_error_message" in content
    assert "project_status_demo_available" in content
    assert "project_status_session_store_preferred_backend" in content
    assert "project_status_session_store_redis_available" in content
    assert "project_status_session_store_degraded_to_sqlite" in content
    assert "project_status_session_store_redis_url" in content
    assert "project_status_session_store_recovered_count" in content
    assert "project_status_session_store_latest_warning_task_id" in content
    assert "project_status_session_store_latest_warning_at" in content
    assert "project_status_session_store_latest_recovered_task_id" in content
    assert "project_status_session_store_latest_recovered_at" in content
    assert "project_status_latest_task_has_llm_judgement" in content
    assert "project_status_latest_task_judgement_issue_count" in content
    assert "project_status_latest_task_tool_call_log_count" in content
    assert "project_status_latest_task_eval_issue_count" in content
    assert "project_status_latest_task_planned_tool_call_count" in content
    assert "project_status_latest_task_event_count" in content
    assert "project_status_latest_task_business_suggestion_count" in content
    assert "project_status_latest_task_data_limitation_count" in content
    assert "project_status_latest_task_top_business_context_title" in content
    assert "project_status_latest_task_top_business_context_embedding_score" in content
    assert "project_status_latest_task_top_business_context_rerank_score" in content
    assert "project_status_latest_task_top_business_context_retrieval_sources" in content
    assert "project_status_latest_task_checkpoint_draft_report_status" in content
    assert "project_status_latest_task_completed_step_count" in content
    assert "project_status_latest_task_metric_count" in content
    assert "project_status_latest_task_successful_tool_result_count" in content
    assert "project_status_latest_task_failed_tool_result_count" in content
    assert "project_status_latest_task_latest_retry_status" in content
    assert "project_status_latest_task_latest_error_code" in content
    assert "project_status_files" in content
    assert "project_status_tasks" in content
    assert "project_status_analysis_events" in content
    assert "project_status_tool_call_logs" in content
    assert "project_status_eval_results" in content
    assert "project_status_files_exists" in content
    assert "project_status_tasks_exists" in content
    assert "project_status_analysis_events_exists" in content
    assert "project_status_tool_call_logs_exists" in content
    assert "project_status_eval_results_exists" in content
    assert "provider_status_allow_fallback" in content
    assert "provider_status_has_api_key" in content
    assert "provider_status_key_source" in content
    assert "provider_status_base_url" in content
    assert "provider_status_model" in content
    assert "provider_status_timeout_seconds" in content
    assert "provider_status_provider_supported" in content
    assert "provider_status_key_source_kind" in content
    assert "provider_status_smoke_ready" in content
    assert "provider_status_warnings" in content
    assert "provider_status_recommendations" in content
    assert "provider_smoke_ok" in content
    assert "provider_smoke_client_type" in content
    assert "provider_smoke_error_type" in content
    assert "fixed_eval_average_trace_completeness" in content
    assert "fixed_eval_retried_tool_calls" in content
    assert "fixed_eval_retry_attempts_total" in content
    assert "fixed_eval_average_tool_elapsed_ms_total" in content
    assert "fixed_eval_average_chart_validity" in content
    assert "fixed_eval_average_field_validity" in content
    assert "fixed_eval_pass_rate" in content
    assert "fixed_eval_passed_cases" in content
    assert "fixed_eval_total_cases" in content
    assert "fixed_eval_average_tool_success_rate" in content


def test_root_readme_matches_current_runtime_truth():
    content = (Path(__file__).resolve().parents[2] / "README.md").read_text(
        encoding="utf-8"
    )

    assert "docs/RESUME_EVIDENCE_MAP.md" in content
    assert "docs/INTERVIEW_DEMO_CHECKLIST.md" in content
    assert "docs/INTERVIEW_DEMO_PREFLIGHT.md" in content
    assert "docs/RELEASE_READINESS_AUDIT.md" in content
    assert "真实 Tongyi Qianwen Provider" in content or "真实通义千问 Provider" in content
    assert "GET /api/project-status" in content
    assert "advanced_code_execution" in content
    assert "/api/sandbox/status" in content
    assert "/api/sandbox/execute" in content
    assert "demo_mvp.ps1" in content
    assert "未实现真实 LLM Provider" not in content
    assert "当前没有实现 DockerSandbox" not in content
    assert "provider_smoke_error_message" in content
    assert "project_status_latest_task_has_context_checkpoint" in content
    assert "project_status_latest_task_eval_has_dimension_scores" in content
    assert "project_status_latest_task_latest_event_at" in content
    assert "project_status_latest_task_llm_issue_count" in content
    assert "project_status_latest_task_next_step_count" in content
    assert "project_status_latest_task_checkpoint_latest_error_code" in content
    assert "project_status_latest_task_current_step" in content
    assert "project_status_latest_task_finding_count" in content
    assert "project_status_latest_task_latest_finding_summary" in content
    assert "project_status_latest_task_latest_tool_name" in content
    assert "project_status_latest_task_top_key_finding" in content
    assert "project_status_latest_task_latest_error_message" in content
    assert "project_status_demo_available" in content
    assert "project_status_session_store_preferred_backend" in content
    assert "project_status_session_store_redis_available" in content
    assert "project_status_session_store_degraded_to_sqlite" in content
    assert "project_status_session_store_redis_url" in content
    assert "project_status_session_store_recovered_count" in content
    assert "project_status_session_store_latest_warning_task_id" in content
    assert "project_status_session_store_latest_warning_at" in content
    assert "project_status_session_store_latest_recovered_task_id" in content
    assert "project_status_session_store_latest_recovered_at" in content
    assert "project_status_latest_task_has_llm_judgement" in content
    assert "project_status_latest_task_judgement_issue_count" in content
    assert "project_status_latest_task_tool_call_log_count" in content
    assert "project_status_latest_task_eval_issue_count" in content
    assert "project_status_latest_task_planned_tool_call_count" in content
    assert "project_status_latest_task_event_count" in content
    assert "project_status_latest_task_business_suggestion_count" in content
    assert "project_status_latest_task_data_limitation_count" in content
    assert "project_status_latest_task_top_business_context_title" in content
    assert "project_status_latest_task_checkpoint_draft_report_status" in content
    assert "project_status_latest_task_completed_step_count" in content
    assert "project_status_latest_task_metric_count" in content
    assert "project_status_latest_task_successful_tool_result_count" in content
    assert "project_status_latest_task_failed_tool_result_count" in content
    assert "project_status_latest_task_latest_retry_status" in content
    assert "project_status_latest_task_latest_error_code" in content
    assert "project_status_files" in content
    assert "project_status_tasks" in content
    assert "project_status_analysis_events" in content
    assert "project_status_tool_call_logs" in content
    assert "project_status_eval_results" in content
    assert "project_status_files_exists" in content
    assert "project_status_tasks_exists" in content
    assert "project_status_analysis_events_exists" in content
    assert "project_status_tool_call_logs_exists" in content
    assert "project_status_eval_results_exists" in content
    assert "provider_status_allow_fallback" in content
    assert "provider_status_has_api_key" in content
    assert "provider_status_key_source" in content
    assert "provider_status_base_url" in content
    assert "provider_status_model" in content
    assert "provider_status_timeout_seconds" in content
    assert "provider_status_provider_supported" in content
    assert "provider_status_key_source_kind" in content
    assert "provider_status_smoke_ready" in content
    assert "provider_status_warnings" in content
    assert "provider_status_recommendations" in content
    assert "provider_smoke_ok" in content
    assert "provider_smoke_client_type" in content
    assert "provider_smoke_error_type" in content
    assert "fixed_eval_average_report_completeness" in content
    assert "fixed_eval_average_tool_elapsed_ms_total" in content
    assert "fixed_eval_average_chart_validity" in content
    assert "fixed_eval_average_field_validity" in content
    assert "fixed_eval_pass_rate" in content
    assert "fixed_eval_passed_cases" in content
    assert "fixed_eval_total_cases" in content
    assert "fixed_eval_average_tool_success_rate" in content
    assert "session store" in content.lower() or "Redis 优先" in content


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


def test_delivery_docs_mention_real_redis_memory_runtime_evidence():
    repo_root = Path(__file__).resolve().parents[2]
    resume_description = (repo_root / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(encoding="utf-8")
    evidence_map = (repo_root / "docs" / "RESUME_EVIDENCE_MAP.md").read_text(encoding="utf-8")
    project_status = (repo_root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "memory_context" in resume_description
    assert "sliding window" in resume_description
    assert "summary_memory" in resume_description
    assert "summary_text" in resume_description

    assert "memory_context" in evidence_map
    assert "recent_turns" in evidence_map
    assert "summary_memory" in evidence_map
    assert "project_status_latest_task_recent_turn_count" in evidence_map

    assert "memory_context" in project_status
    assert "recent_turns" in project_status
    assert "summary_memory" in project_status
    assert "summary_text" in project_status


def test_delivery_docs_mention_structured_llm_judge_runtime_evidence():
    repo_root = Path(__file__).resolve().parents[2]
    resume_description = (repo_root / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(encoding="utf-8")
    evidence_map = (repo_root / "docs" / "RESUME_EVIDENCE_MAP.md").read_text(encoding="utf-8")
    project_status = (repo_root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")

    assert "LLM-as-Judge" in resume_description
    assert "judge_summary" in resume_description
    assert "judge_status" in resume_description
    assert "groundedness" in resume_description
    assert "completeness" in resume_description
    assert "clarity" in resume_description

    assert "LLM-as-Judge" in evidence_map
    assert "judge_summary" in evidence_map
    assert "judge_status" in evidence_map
    assert "groundedness" in evidence_map
    assert "completeness" in evidence_map
    assert "clarity" in evidence_map

    assert "LLM-As-Judge" in project_status or "LLM-as-Judge" in project_status
    assert "judge_summary" in project_status
    assert "judge_status" in project_status
    assert "groundedness" in project_status
    assert "completeness" in project_status
    assert "clarity" in project_status


def test_delivery_docs_mention_docker_sandbox_runtime_evidence():
    repo_root = Path(__file__).resolve().parents[2]
    resume_description = (repo_root / "docs" / "RESUME_PROJECT_DESCRIPTION.md").read_text(encoding="utf-8")
    interview_guide = (repo_root / "docs" / "INTERVIEW_GUIDE.md").read_text(encoding="utf-8")
    release_readiness = (repo_root / "docs" / "RELEASE_READINESS_AUDIT.md").read_text(encoding="utf-8")
    evidence_map = (repo_root / "docs" / "RESUME_EVIDENCE_MAP.md").read_text(encoding="utf-8")

    assert "DockerSandbox" in resume_description
    assert "advanced_code_execution" in resume_description
    assert "/api/sandbox/execute" in resume_description
    assert "/api/sandbox/status" in resume_description
    assert "latest sandbox runtime evidence" in resume_description
    assert "SANDBOX_SYNTAX_ERROR" in resume_description
    assert "SANDBOX_NETWORK_ERROR" in resume_description
    assert "SANDBOX_RESOURCE_KILLED" in resume_description
    assert "region_sales_summary" in resume_description
    assert "supported_templates" in resume_description
    assert "max_code_chars" in resume_description
    assert "template_name" in resume_description
    assert "parsed_output_keys" in resume_description
    assert "configured runtime ceiling" in resume_description
    assert "当前没有实现 DockerSandbox" not in interview_guide
    assert "/api/sandbox/execute" in interview_guide
    assert "/api/sandbox/status" in interview_guide
    assert "latest sandbox execution evidence" in interview_guide
    assert "SANDBOX_IMPORT_ERROR" in interview_guide
    assert "SANDBOX_NETWORK_ERROR" in interview_guide
    assert "template-backed sandbox execution" in interview_guide
    assert "当前仍未实现、因此不应作为封板完成项对外声称的内容包括：\n\n- DockerSandbox" not in release_readiness
    assert "sandbox_execution_logs" in evidence_map
    assert "SANDBOX_PERMISSION_ERROR" in evidence_map
    assert "SANDBOX_RESOURCE_KILLED" in evidence_map
    assert "region_sales_summary" in evidence_map
    assert "supported_templates" in evidence_map
    assert "max_code_chars" in evidence_map
    assert "python_code_char_count" in evidence_map
    assert "template_result_field_count" in evidence_map


def test_interview_guide_mentions_demo_script_diagnostic_outputs():
    content = (Path(__file__).resolve().parents[2] / "docs" / "INTERVIEW_GUIDE.md").read_text(
        encoding="utf-8"
    )

    assert "RESUME_EVIDENCE_MAP.md" in content
    assert "INTERVIEW_DEMO_CHECKLIST.md" in content
    assert "INTERVIEW_DEMO_PREFLIGHT.md" in content
    assert "RELEASE_READINESS_AUDIT.md" in content
    assert "demo_mvp.ps1" in content
    assert "/api/sandbox/status" in content
    assert "/api/sandbox/execute" in content
    assert "当前没有实现 DockerSandbox" not in content
    assert "真实 Plotly" in content or "plotly_spec" in content
    assert "缺少可用 API key" in content
    assert "analysis_state" in content
    assert "细粒度 Redis key" in content
    assert "provider smoke" in content or "provider smoke failed" in content or "provider 解析结果" in content
    assert "fixed eval" in content or "质量指标" in content
    assert "project_status_latest_task_has_context_checkpoint" in content
    assert "project_status_latest_task_eval_has_dimension_scores" in content
    assert "project_status_latest_task_latest_event_at" in content
    assert "project_status_latest_task_llm_issue_count" in content
    assert "project_status_latest_task_next_step_count" in content
    assert "project_status_latest_task_checkpoint_latest_error_code" in content
    assert "project_status_latest_task_current_step" in content
    assert "project_status_latest_task_finding_count" in content
    assert "project_status_latest_task_latest_finding_summary" in content
    assert "project_status_latest_task_latest_tool_name" in content
    assert "project_status_latest_task_top_key_finding" in content
    assert "project_status_latest_task_latest_error_message" in content
    assert "project_status_demo_available" in content
    assert "project_status_session_store_preferred_backend" in content
    assert "project_status_session_store_redis_available" in content
    assert "project_status_session_store_degraded_to_sqlite" in content
    assert "project_status_session_store_redis_url" in content
    assert "project_status_session_store_recovered_count" in content
    assert "project_status_session_store_latest_warning_task_id" in content
    assert "project_status_session_store_latest_warning_at" in content
    assert "project_status_session_store_latest_recovered_task_id" in content
    assert "project_status_session_store_latest_recovered_at" in content
    assert "project_status_latest_task_has_llm_judgement" in content
    assert "project_status_latest_task_judgement_issue_count" in content
    assert "project_status_latest_task_tool_call_log_count" in content
    assert "project_status_latest_task_eval_issue_count" in content
    assert "project_status_latest_task_planned_tool_call_count" in content
    assert "project_status_latest_task_event_count" in content
    assert "project_status_latest_task_business_suggestion_count" in content
    assert "project_status_latest_task_data_limitation_count" in content
    assert "project_status_latest_task_top_business_context_title" in content
    assert "project_status_latest_task_checkpoint_draft_report_status" in content
    assert "project_status_latest_task_completed_step_count" in content
    assert "project_status_latest_task_metric_count" in content
    assert "project_status_latest_task_successful_tool_result_count" in content
    assert "project_status_latest_task_failed_tool_result_count" in content
    assert "project_status_latest_task_latest_retry_status" in content
    assert "project_status_latest_task_latest_error_code" in content
    assert "project_status_files" in content
    assert "project_status_tasks" in content
    assert "project_status_analysis_events" in content
    assert "project_status_tool_call_logs" in content
    assert "project_status_eval_results" in content
    assert "project_status_files_exists" in content
    assert "project_status_tasks_exists" in content
    assert "project_status_analysis_events_exists" in content
    assert "project_status_tool_call_logs_exists" in content
    assert "project_status_eval_results_exists" in content
    assert "provider_status_allow_fallback" in content
    assert "provider_status_has_api_key" in content
    assert "provider_status_key_source" in content
    assert "provider_status_base_url" in content
    assert "provider_status_model" in content
    assert "provider_status_timeout_seconds" in content
    assert "provider_status_provider_supported" in content
    assert "provider_status_key_source_kind" in content
    assert "provider_status_smoke_ready" in content
    assert "provider_status_warnings" in content
    assert "provider_status_recommendations" in content
    assert "provider_smoke_ok" in content
    assert "provider_smoke_client_type" in content
    assert "provider_smoke_error_type" in content
    assert "fixed_eval_retried_tool_calls" in content
    assert "fixed_eval_retry_attempts_total" in content
    assert "fixed_eval_average_tool_elapsed_ms_total" in content
    assert "fixed_eval_average_chart_validity" in content
    assert "fixed_eval_average_field_validity" in content
    assert "fixed_eval_pass_rate" in content
    assert "fixed_eval_passed_cases" in content
    assert "fixed_eval_total_cases" in content
    assert "fixed_eval_average_tool_success_rate" in content
    assert "session store" in content.lower() or "Redis 优先" in content
