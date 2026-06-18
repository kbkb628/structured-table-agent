param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$StartServer
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $repoRoot "backend"
$pythonPath = Join-Path $backendDir ".venv\Scripts\python.exe"
$samplePath = Join-Path $backendDir "data\samples\sales_orders.csv"

if (-not (Test-Path $samplePath)) {
    throw "Sample CSV not found: $samplePath"
}

$serverProcess = $null

function Wait-ServerReady {
    param([string]$HealthUrl)

    for ($i = 0; $i -lt 20; $i++) {
        try {
            Invoke-RestMethod -Method Get -Uri $HealthUrl | Out-Null
            return
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }

    throw "Server did not become ready in time: $HealthUrl"
}

try {
    if ($StartServer) {
        if (-not (Test-Path $pythonPath)) {
            throw "Python venv not found: $pythonPath"
        }

        $serverProcess = Start-Process `
            -FilePath $pythonPath `
            -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" `
            -WorkingDirectory $backendDir `
            -WindowStyle Hidden `
            -PassThru

        Wait-ServerReady -HealthUrl "$BaseUrl/docs"
    }

    $projectStatus = Invoke-RestMethod `
        -Method Get `
        -Uri "$BaseUrl/api/project-status"

    $providerStatus = Invoke-RestMethod `
        -Method Get `
        -Uri "$BaseUrl/api/llm/provider-status"

    $providerSmoke = Invoke-RestMethod `
        -Method Post `
        -Uri "$BaseUrl/api/llm/provider-smoke"

    $uploadRaw = & curl.exe -s -X POST -F "file=@$samplePath" "$BaseUrl/api/files/upload"
    if (-not $uploadRaw) {
        throw "Upload request returned an empty response."
    }

    $upload = $uploadRaw | ConvertFrom-Json

    $questions = @(
        "analyse category sales top 5",
        "analyse category sales share",
        "analyse category sales anomalies",
        "analyse sales by region",
        "analyse sales trend by order date",
        "analyse channel order count and sales performance"
    )

    $runs = foreach ($question in $questions) {
        $start = Invoke-RestMethod `
            -Method Post `
            -Uri "$BaseUrl/api/analysis/start" `
            -ContentType "application/json" `
            -Body (@{ file_id = $upload.file_id; question = $question } | ConvertTo-Json)

        $run = Invoke-RestMethod `
            -Method Post `
            -Uri "$BaseUrl/api/analysis/$($start.task_id)/run"

        [pscustomobject]@{
            question = $question
            task_id = $start.task_id
            status = $run.status
            tool_results = $run.tool_results.Count
            chart_specs = $run.chart_specs.Count
            eval_score = $run.eval_result.overall_score
            key_findings = $run.final_report.key_findings.Count
        }
    }

    $rerunEval = Invoke-RestMethod `
        -Method Post `
        -Uri "$BaseUrl/api/eval/run" `
        -ContentType "application/json" `
        -Body (@{ task_id = $runs[-1].task_id } | ConvertTo-Json)

    $fixedEval = Invoke-RestMethod `
        -Method Post `
        -Uri "$BaseUrl/api/eval/cases/run"

    [pscustomobject]@{
        upload_file_id = $upload.file_id
        upload_rows = $upload.row_count
        upload_columns = $upload.column_count
        project_status_provider = $projectStatus.summary.provider.provider
        project_status_demo_available = $projectStatus.summary.demo.available
        project_status_demo_path = $projectStatus.summary.demo.path
        project_status_latest_task_id = $projectStatus.summary.latest_task.task_id
        project_status_latest_task_status = $projectStatus.summary.latest_task.status
        project_status_latest_task_updated_at = $projectStatus.summary.latest_task.updated_at
        project_status_session_store_preferred_backend = $projectStatus.summary.session_store.preferred_backend
        project_status_session_store_active_backend = $projectStatus.summary.session_store.active_backend
        project_status_session_store_redis_available = $projectStatus.summary.session_store.redis_available
        project_status_session_store_degraded_to_sqlite = $projectStatus.summary.session_store.degraded_to_sqlite
        project_status_session_store_redis_url = $projectStatus.summary.session_store.redis_url
        project_status_session_store_warning_count = $projectStatus.summary.session_store.event_summary.warning_count
        project_status_session_store_recovered_count = $projectStatus.summary.session_store.event_summary.recovered_count
        project_status_session_store_latest_warning_task_id = $projectStatus.summary.session_store.event_summary.latest_warning_task_id
        project_status_session_store_latest_warning_at = $projectStatus.summary.session_store.event_summary.latest_warning_at
        project_status_session_store_latest_recovered_task_id = $projectStatus.summary.session_store.event_summary.latest_recovered_task_id
        project_status_session_store_latest_recovered_at = $projectStatus.summary.session_store.event_summary.latest_recovered_at
        project_status_session_store_latest_recovered_recovery_source = $projectStatus.summary.session_store.event_summary.latest_recovered_recovery_source
        project_status_session_store_latest_recovered_segment_count = $projectStatus.summary.session_store.event_summary.latest_recovered_segment_count
        project_status_session_store_latest_recovered_segments = $projectStatus.summary.session_store.event_summary.latest_recovered_segments
        project_status_latest_task_has_business_context = $projectStatus.summary.latest_task.artifacts.has_business_context
        project_status_latest_task_has_context_checkpoint = $projectStatus.summary.latest_task.artifacts.has_context_checkpoint
        project_status_latest_task_has_draft_report = $projectStatus.summary.latest_task.artifacts.has_draft_report
        project_status_latest_task_has_final_report = $projectStatus.summary.latest_task.artifacts.has_final_report
        project_status_latest_task_has_llm_judgement = $projectStatus.summary.latest_task.artifacts.has_llm_judgement
        project_status_latest_task_supported_by_tools = $projectStatus.summary.latest_task.judgement.supported_by_tools
        project_status_latest_task_has_findings = $projectStatus.summary.latest_task.judgement.has_findings
        project_status_latest_task_judgement_issue_count = $projectStatus.summary.latest_task.judgement.issue_count
        project_status_latest_task_tool_call_log_count = $projectStatus.summary.latest_task.artifacts.tool_call_log_count
        project_status_latest_task_has_eval_result = $projectStatus.summary.latest_task.evaluation.has_eval_result
        project_status_latest_task_eval_overall_score = $projectStatus.summary.latest_task.evaluation.overall_score
        project_status_latest_task_eval_issue_count = $projectStatus.summary.latest_task.evaluation.issue_count
        project_status_latest_task_eval_suggestion_count = $projectStatus.summary.latest_task.evaluation.suggestion_count
        project_status_latest_task_eval_has_dimension_scores = $projectStatus.summary.latest_task.evaluation.has_dimension_scores
        project_status_latest_task_eval_schema_valid = $projectStatus.summary.latest_task.evaluation.schema_valid
        project_status_latest_task_eval_tool_success_rate = $projectStatus.summary.latest_task.evaluation.tool_success_rate
        project_status_latest_task_eval_tool_elapsed_ms_total = $projectStatus.summary.latest_task.evaluation.tool_elapsed_ms_total
        project_status_latest_task_eval_field_validity = $projectStatus.summary.latest_task.evaluation.field_validity
        project_status_latest_task_eval_chart_validity = $projectStatus.summary.latest_task.evaluation.chart_validity
        project_status_latest_task_eval_report_completeness = $projectStatus.summary.latest_task.evaluation.report_completeness
        project_status_latest_task_eval_trace_completeness = $projectStatus.summary.latest_task.evaluation.trace_completeness
        project_status_latest_task_pending_metric_count = $projectStatus.summary.latest_task.process.pending_metric_count
        project_status_latest_task_planned_tool_call_count = $projectStatus.summary.latest_task.process.planned_tool_call_count
        project_status_latest_task_event_count = $projectStatus.summary.latest_task.process.event_count
        project_status_latest_task_latest_event_type = $projectStatus.summary.latest_task.process.latest_event_type
        project_status_latest_task_latest_event_at = $projectStatus.summary.latest_task.process.latest_event_at
        project_status_latest_task_llm_issue_count = $projectStatus.summary.latest_task.process.llm_issue_count
        project_status_latest_task_route_decision_count = $projectStatus.summary.latest_task.process.route_decision_count
        project_status_latest_task_continued_route_decision_count = $projectStatus.summary.latest_task.process.continued_route_decision_count
        project_status_latest_task_finished_route_decision_count = $projectStatus.summary.latest_task.process.finished_route_decision_count
        project_status_latest_task_latest_route_decision = $projectStatus.summary.latest_task.process.latest_route_decision
        project_status_latest_task_chart_spec_count = $projectStatus.summary.latest_task.report.chart_spec_count
        project_status_latest_task_key_finding_count = $projectStatus.summary.latest_task.report.key_finding_count
        project_status_latest_task_business_suggestion_count = $projectStatus.summary.latest_task.report.business_suggestion_count
        project_status_latest_task_data_limitation_count = $projectStatus.summary.latest_task.report.data_limitation_count
        project_status_latest_task_next_step_count = $projectStatus.summary.latest_task.report.next_step_count
        project_status_latest_task_business_context_count = $projectStatus.summary.latest_task.context.business_context_count
        project_status_latest_task_top_business_context_title = $projectStatus.summary.latest_task.context.top_business_context_title
        project_status_latest_task_top_business_context_score = $projectStatus.summary.latest_task.context.top_business_context_score
        project_status_latest_task_top_business_context_related_field_count = $projectStatus.summary.latest_task.context.top_business_context_related_field_count
        project_status_latest_task_top_business_context_has_score_breakdown = $projectStatus.summary.latest_task.context.top_business_context_has_score_breakdown
        project_status_latest_task_top_business_context_keyword_score = $projectStatus.summary.latest_task.context.top_business_context_keyword_score
        project_status_latest_task_top_business_context_field_score = $projectStatus.summary.latest_task.context.top_business_context_field_score
        project_status_latest_task_top_business_context_phrase_score = $projectStatus.summary.latest_task.context.top_business_context_phrase_score
        project_status_latest_task_top_business_context_bm25_score = $projectStatus.summary.latest_task.context.top_business_context_bm25_score
        project_status_latest_task_checkpoint_current_step = $projectStatus.summary.latest_task.context.checkpoint_current_step
        project_status_latest_task_checkpoint_status = $projectStatus.summary.latest_task.context.checkpoint_status
        project_status_latest_task_checkpoint_pending_metric_count = $projectStatus.summary.latest_task.context.checkpoint_pending_metric_count
        project_status_latest_task_checkpoint_finding_count = $projectStatus.summary.latest_task.context.checkpoint_finding_count
        project_status_latest_task_checkpoint_business_context_title_count = $projectStatus.summary.latest_task.context.checkpoint_business_context_title_count
        project_status_latest_task_checkpoint_business_context_titles = $projectStatus.summary.latest_task.context.checkpoint_business_context_titles
        project_status_latest_task_checkpoint_draft_report_status = $projectStatus.summary.latest_task.context.checkpoint_draft_report_status
        project_status_latest_task_checkpoint_latest_error_code = $projectStatus.summary.latest_task.context.checkpoint_latest_error_code
        project_status_latest_task_analysis_goal = $projectStatus.summary.latest_task.semantics.analysis_goal
        project_status_latest_task_analysis_plan_count = $projectStatus.summary.latest_task.semantics.analysis_plan_count
        project_status_latest_task_current_step = $projectStatus.summary.latest_task.semantics.current_step
        project_status_latest_task_completed_step_count = $projectStatus.summary.latest_task.semantics.completed_step_count
        project_status_latest_task_finding_count = $projectStatus.summary.latest_task.semantics.finding_count
        project_status_latest_task_dimension_field = $projectStatus.summary.latest_task.semantics.dimension_field
        project_status_latest_task_metric_count = $projectStatus.summary.latest_task.semantics.metric_count
        project_status_latest_task_match_analysis_type = $projectStatus.summary.latest_task.semantics.match_analysis_type
        project_status_latest_task_candidate_field_count = $projectStatus.summary.latest_task.semantics.candidate_field_count
        project_status_latest_task_match_warning_count = $projectStatus.summary.latest_task.semantics.match_warning_count
        project_status_latest_task_planned_tool_sequence = $projectStatus.summary.latest_task.semantics.planned_tool_sequence
        project_status_latest_task_tool_result_count = $projectStatus.summary.latest_task.tools.tool_result_count
        project_status_latest_task_successful_tool_result_count = $projectStatus.summary.latest_task.tools.successful_tool_result_count
        project_status_latest_task_failed_tool_result_count = $projectStatus.summary.latest_task.tools.failed_tool_result_count
        project_status_latest_task_total_tool_elapsed_ms = $projectStatus.summary.latest_task.tools.total_tool_elapsed_ms
        project_status_latest_task_retried_tool_result_count = $projectStatus.summary.latest_task.tools.retried_tool_result_count
        project_status_latest_task_retry_attempts_total = $projectStatus.summary.latest_task.tools.retry_attempts_total
        project_status_latest_task_latest_tool_name = $projectStatus.summary.latest_task.tools.latest_tool_name
        project_status_latest_task_latest_retry_status = $projectStatus.summary.latest_task.tools.latest_retry_status
        project_status_latest_task_error_count = $projectStatus.summary.latest_task.errors.error_count
        project_status_latest_task_latest_error_code = $projectStatus.summary.latest_task.errors.latest_error_code
        project_status_latest_task_latest_error_message = $projectStatus.summary.latest_task.errors.latest_error_message
        project_status_latest_task_has_degradation = $projectStatus.summary.latest_task.errors.has_degradation
        project_status_files_exists = $projectStatus.summary.database.tables.files.exists
        project_status_tasks_exists = $projectStatus.summary.database.tables.analysis_tasks.exists
        project_status_analysis_events_exists = $projectStatus.summary.database.tables.analysis_events.exists
        project_status_tool_call_logs_exists = $projectStatus.summary.database.tables.tool_call_logs.exists
        project_status_eval_results_exists = $projectStatus.summary.database.tables.eval_results.exists
        project_status_files = $projectStatus.summary.database.tables.files.row_count
        project_status_tasks = $projectStatus.summary.database.tables.analysis_tasks.row_count
        project_status_analysis_events = $projectStatus.summary.database.tables.analysis_events.row_count
        project_status_tool_call_logs = $projectStatus.summary.database.tables.tool_call_logs.row_count
        project_status_eval_results = $projectStatus.summary.database.tables.eval_results.row_count
        provider_status_allow_fallback = $providerStatus.allow_fallback
        provider_status_has_api_key = $providerStatus.has_api_key
        provider_status_key_source = $providerStatus.api_key_source
        provider_status_base_url = $providerStatus.base_url
        provider_status_model = $providerStatus.model
        provider_status_timeout_seconds = $providerStatus.timeout_seconds
        provider_status_provider_supported = $providerStatus.diagnostics.provider_supported
        provider_status_key_source_kind = $providerStatus.diagnostics.key_source_kind
        provider_status_smoke_ready = $providerStatus.diagnostics.smoke_ready
        provider_status_warnings = $providerStatus.diagnostics.warnings
        provider_status_recommendations = $providerStatus.diagnostics.recommendations
        provider_smoke_ok = $providerSmoke.ok
        provider_smoke_client_type = $providerSmoke.client_type
        provider_smoke_error_type = $providerSmoke.error_type
        provider_smoke_error_message = $providerSmoke.error_message
        fixed_eval_pass_rate = $fixedEval.pass_rate
        fixed_eval_passed_cases = $fixedEval.passed_cases
        fixed_eval_total_cases = $fixedEval.total_cases
        fixed_eval_retried_tool_calls = $fixedEval.retried_tool_calls
        fixed_eval_retry_attempts_total = $fixedEval.retry_attempts_total
        fixed_eval_average_tool_elapsed_ms_total = $fixedEval.average_tool_elapsed_ms_total
        fixed_eval_average_trace_completeness = $fixedEval.average_trace_completeness
        fixed_eval_average_report_completeness = $fixedEval.average_report_completeness
        fixed_eval_average_tool_success_rate = $fixedEval.average_tool_success_rate
        fixed_eval_average_chart_validity = $fixedEval.average_chart_validity
        fixed_eval_average_field_validity = $fixedEval.average_field_validity
        runs = $runs
        rerun_eval_task = $rerunEval.task_id
        rerun_eval_score = $rerunEval.eval_result.overall_score
    } | ConvertTo-Json -Depth 6
} finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force
    }
}
