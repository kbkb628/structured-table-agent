from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter(tags=["demo"])


@router.get("/demo", response_class=HTMLResponse)
def demo_page() -> HTMLResponse:
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Structured Table Analysis Demo</title>
  <style>
    :root {
      --bg: #f4efe6;
      --panel: #fffaf1;
      --ink: #1f1d1a;
      --muted: #6f675b;
      --accent: #125b50;
      --accent-2: #f0a04b;
      --line: #d8ccb8;
      --ok: #1f7a4f;
      --warn: #a44b1a;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at top left, rgba(240,160,75,0.16), transparent 28%),
        linear-gradient(135deg, #efe7da 0%, var(--bg) 45%, #f7f2e9 100%);
      color: var(--ink);
    }
    .page {
      max-width: 1180px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      display: grid;
      gap: 14px;
      margin-bottom: 24px;
    }
    .eyebrow {
      color: var(--accent);
      font-size: 0.82rem;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }
    h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.6rem);
      line-height: 1.02;
    }
    .intro {
      max-width: 760px;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.6;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(320px, 420px) 1fr;
      gap: 18px;
    }
    .panel {
      background: rgba(255, 250, 241, 0.92);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: 0 14px 30px rgba(31, 29, 26, 0.08);
      overflow: hidden;
    }
    .panel-header {
      padding: 18px 20px 10px;
      border-bottom: 1px solid rgba(216, 204, 184, 0.7);
    }
    .panel-header h2 {
      margin: 0;
      font-size: 1.15rem;
    }
    .panel-body {
      padding: 18px 20px 20px;
      display: grid;
      gap: 14px;
    }
    label {
      display: grid;
      gap: 8px;
      font-size: 0.95rem;
      color: var(--muted);
    }
    input[type="file"], input[type="text"], textarea, button, select {
      font: inherit;
    }
    input[type="text"], textarea {
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: #fffdf8;
      color: var(--ink);
    }
    textarea {
      min-height: 110px;
      resize: vertical;
    }
    .button-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 11px 18px;
      cursor: pointer;
      font-weight: 700;
      transition: transform 120ms ease, opacity 120ms ease;
    }
    button:hover { transform: translateY(-1px); }
    button:disabled { cursor: wait; opacity: 0.6; transform: none; }
    .primary { background: var(--accent); color: #fff; }
    .secondary { background: var(--accent-2); color: #2d2417; }
    .ghost { background: #efe4d2; color: var(--ink); }
    .chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .chip {
      border: 1px solid var(--line);
      background: #f9f2e7;
      border-radius: 999px;
      padding: 7px 12px;
      font-size: 0.86rem;
      color: var(--muted);
      cursor: pointer;
    }
    .status {
      padding: 12px 14px;
      border-radius: 14px;
      background: #f7f0e4;
      color: var(--ink);
      border: 1px solid var(--line);
      line-height: 1.5;
      white-space: pre-wrap;
    }
    .status strong { color: var(--accent); }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }
    .summary-card {
      border: 1px solid var(--line);
      border-radius: 16px;
      background: #fffdf8;
      padding: 12px 14px;
      display: grid;
      gap: 6px;
    }
    .summary-label {
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }
    .summary-value {
      font-size: 1.12rem;
      font-weight: 700;
      color: var(--ink);
    }
    .summary-note {
      font-size: 0.8rem;
      color: var(--muted);
    }
    .provider-grid {
      display: grid;
      gap: 10px;
    }
    .provider-card {
      border: 1px solid var(--line);
      border-radius: 16px;
      background: #fffdf8;
      padding: 12px 14px;
      display: grid;
      gap: 6px;
    }
    .provider-card-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .provider-title {
      font-weight: 700;
      color: var(--ink);
    }
    .provider-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 4px 10px;
      background: #f1eadc;
      color: var(--accent);
      font-size: 0.78rem;
      font-weight: 700;
    }
    .provider-meta {
      color: var(--muted);
      font-size: 0.84rem;
      line-height: 1.5;
    }
    .provider-diag {
      padding: 10px 12px;
      border-radius: 12px;
      border: 1px dashed var(--line);
      background: #fcf7ef;
      font-size: 0.84rem;
      color: var(--muted);
      white-space: pre-wrap;
      line-height: 1.5;
    }
    .eval-shell {
      display: grid;
      gap: 12px;
    }
    .grid {
      display: grid;
      gap: 18px;
    }
    .output-block {
      display: grid;
      gap: 10px;
    }
    .output-block h3 {
      margin: 0;
      font-size: 0.98rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    pre {
      margin: 0;
      padding: 14px;
      min-height: 140px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: #fffdf8;
      overflow: auto;
      font-size: 0.86rem;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .report-list {
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 10px;
      color: var(--ink);
    }
    .report-list li {
      line-height: 1.5;
    }
    .chart-shell {
      display: grid;
      gap: 10px;
      min-height: 220px;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: #fffdf8;
    }
    .chart-meta {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      font-size: 0.84rem;
      color: var(--muted);
    }
    .chart-empty {
      display: grid;
      place-items: center;
      min-height: 160px;
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 12px;
      background: #fcf7ef;
      text-align: center;
      padding: 16px;
    }
    .chart-svg {
      width: 100%;
      height: 180px;
      overflow: visible;
    }
    .chart-line {
      fill: none;
      stroke: var(--accent);
      stroke-width: 3;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .chart-point {
      fill: var(--accent-2);
      stroke: var(--accent);
      stroke-width: 2;
    }
    .chart-bar {
      fill: var(--accent);
      opacity: 0.88;
    }
    .chart-label {
      font-size: 10px;
      fill: var(--muted);
    }
    .chart-value {
      font-size: 10px;
      fill: var(--ink);
    }
    .hint {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.5;
    }
    .fine {
      font-size: 0.82rem;
      color: var(--muted);
    }
    @media (max-width: 920px) {
      .layout { grid-template-columns: 1fr; }
      .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <div class="eyebrow">Structured Table Agent</div>
      <h1>Structured Table Analysis Demo</h1>
      <div class="intro">
        This page is a thin demo shell over the real backend chain. It uploads a CSV or Excel file,
        starts an analysis task, runs the LangGraph workflow, and then polls the persisted task state,
        event timeline, and tool logs from the existing FastAPI APIs.
      </div>
    </section>

    <section class="layout">
      <div class="panel">
        <div class="panel-header">
          <h2>Run Analysis</h2>
        </div>
        <div class="panel-body">
          <form id="upload-form">
            <label>
              Upload CSV or Excel
              <input id="file-input" name="file" type="file" accept=".csv,.xlsx,.xls" required>
            </label>
          </form>
          <div class="hint">
            Built-in sample data is available for quick verification:
            <span class="fine">`sales_orders.csv` can be loaded into the same upload and analysis flow.</span>
          </div>

          <label>
            Analysis Question
            <textarea id="question-input" placeholder="analyse sales by region">analyse sales by region</textarea>
          </label>

          <div class="chips">
            <button class="chip" type="button" data-question="analyse category sales top 5">TopN</button>
            <button class="chip" type="button" data-question="analyse category sales share">Share</button>
            <button class="chip" type="button" data-question="analyse category sales anomalies">Anomaly</button>
            <button class="chip" type="button" data-question="analyse sales by region">Region</button>
            <button class="chip" type="button" data-question="analyse sales trend by order date">Trend</button>
            <button class="chip" type="button" data-question="analyse channel order count and sales performance">Channel</button>
            <button class="chip" type="button" data-question="分析各品类销售额 Top5，并给出业务建议">中文 TopN</button>
            <button class="chip" type="button" data-question="分析各地区销售额对比，并生成图表">中文地区</button>
            <button class="chip" type="button" data-question="分析不同渠道的订单数量和销售额表现">中文渠道</button>
          </div>

          <div class="button-row">
            <button id="load-sample-button" class="ghost" type="button">Load Built-in Sample</button>
            <button id="upload-button" class="secondary" type="button">1. Upload File</button>
            <button id="run-analysis-button" class="primary" type="button">2. Start And Run</button>
            <button id="refresh-button" class="ghost" type="button">Refresh Task</button>
            <button id="provider-status-button" class="ghost" type="button">LLM Status</button>
            <button id="provider-smoke-button" class="ghost" type="button">LLM Smoke</button>
            <button id="project-status-button" class="ghost" type="button">Project Overview</button>
            <button id="eval-cases-button" class="ghost" type="button">Run Fixed Eval Cases</button>
          </div>

          <div id="task-status" class="status">No file uploaded yet.</div>
          <div id="task-summary" class="summary-grid">
            <div class="summary-card">
              <div class="summary-label">Task</div>
              <div class="summary-value">Not started</div>
              <div class="summary-note">A task ID appears here after creation.</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">Status</div>
              <div class="summary-value">Idle</div>
              <div class="summary-note">Current backend state.</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">Tools</div>
              <div class="summary-value">0</div>
              <div class="summary-note">Successful tool results.</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">Score</div>
              <div class="summary-value">-</div>
              <div class="summary-note">Rule-based overall score.</div>
            </div>
          </div>
          <div class="hint">
            The page uses existing APIs only:
            <span class="fine">`/api/files/upload`, `/api/analysis/start`, `/api/analysis/{task_id}/run`, `/api/analysis/{task_id}`, `/events`, `/tool-logs`.</span>
          </div>
          <div class="provider-grid">
            <div class="provider-card">
              <div class="provider-card-head">
                <div class="provider-title">LLM Provider Status</div>
                <div id="provider-pill" class="provider-pill">Not loaded</div>
              </div>
              <div id="provider-meta" class="provider-meta">Provider diagnostics will appear here.</div>
              <div id="provider-diag" class="provider-diag">No provider status loaded yet.</div>
            </div>
            <div class="provider-card">
              <div class="provider-card-head">
                <div class="provider-title">Project Runtime Overview</div>
                <div id="project-status-pill" class="provider-pill">Not loaded</div>
              </div>
              <div id="project-status-meta" class="provider-meta">Runtime summary will appear here.</div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Session Store Runtime Mode</div>
                  <div id="session-store-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="session-store-meta" class="provider-meta">Redis-first / SQLite-fallback summary will appear here.</div>
                <div id="session-store-output" class="provider-diag">No session store runtime summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Artifacts</div>
                  <div id="latest-task-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-meta" class="provider-meta">Latest persisted task artifact coverage will appear here.</div>
                <div id="latest_task_artifacts_output" class="provider-diag">No latest task artifact summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Evaluation</div>
                  <div id="latest-task-eval-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-eval-meta" class="provider-meta">Latest persisted eval_result summary will appear here.</div>
                <div id="latest_task_eval_output" class="provider-diag">No latest task evaluation summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Judgement</div>
                  <div id="latest-task-judgement-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-judgement-meta" class="provider-meta">Latest supplementary llm_judgement summary will appear here.</div>
                <div id="latest_task_judgement_output" class="provider-diag">No latest task judgement summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Process</div>
                  <div id="latest-task-process-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-process-meta" class="provider-meta">Latest task trace and state summary will appear here.</div>
                <div id="latest_task_process_output" class="provider-diag">No latest task process summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Report</div>
                  <div id="latest-task-report-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-report-meta" class="provider-meta">Latest report richness summary will appear here.</div>
                <div id="latest_task_report_output" class="provider-diag">No latest task report summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Context</div>
                  <div id="latest-task-context-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-context-meta" class="provider-meta">Latest RAG and checkpoint summary will appear here.</div>
                <div id="latest_task_context_output" class="provider-diag">No latest task context summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Semantics</div>
                  <div id="latest-task-semantics-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-semantics-meta" class="provider-meta">Latest task goal and planning summary will appear here.</div>
                <div id="latest_task_semantics_output" class="provider-diag">No latest task semantics summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Tools</div>
                  <div id="latest-task-tools-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-tools-meta" class="provider-meta">Latest tool execution summary will appear here.</div>
                <div id="latest_task_tools_output" class="provider-diag">No latest task tool summary loaded yet.</div>
              </div>
              <div class="provider-card">
                <div class="provider-card-head">
                  <div class="provider-title">Latest Task Errors</div>
                  <div id="latest-task-errors-pill" class="provider-pill">Not loaded</div>
                </div>
                <div id="latest-task-errors-meta" class="provider-meta">Latest failure and degradation summary will appear here.</div>
                <div id="latest_task_errors_output" class="provider-diag">No latest task error summary loaded yet.</div>
              </div>
              <div id="project-status-summary" class="summary-grid">
                <div class="summary-card">
                  <div class="summary-label">Demo</div>
                  <div class="summary-value">-</div>
                  <div class="summary-note">Demo availability is loaded from project status.</div>
                </div>
                <div class="summary-card">
                  <div class="summary-label">Files</div>
                  <div class="summary-value">0</div>
                  <div class="summary-note">Persisted upload records.</div>
                </div>
                <div class="summary-card">
                  <div class="summary-label">Tasks</div>
                  <div class="summary-value">0</div>
                  <div class="summary-note">Persisted analysis task rows.</div>
                </div>
                <div class="summary-card">
                  <div class="summary-label">Events</div>
                  <div class="summary-value">0</div>
                  <div class="summary-note">Persisted execution timeline rows.</div>
                </div>
              </div>
              <div id="project-status-output" class="provider-diag">No project runtime overview loaded yet.</div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid">
        <div class="panel">
          <div class="panel-header">
            <h2>Task Outputs</h2>
          </div>
          <div class="panel-body">
            <div class="output-block">
              <h3>Chart Preview</h3>
              <div id="chart-preview" class="chart-shell">
                <div class="chart-meta">
                  <span>Chart preview uses the persisted `chart_specs` output.</span>
                </div>
                <div id="chart-empty-state" class="chart-empty">No chart is available until a completed task returns chart specs.</div>
              </div>
            </div>
            <div class="output-block">
              <h3>Report Highlights</h3>
              <ol id="report-list" class="report-list">
                <li>No report findings yet.</li>
              </ol>
            </div>
            <div class="output-block">
              <h3>Final Report</h3>
              <pre id="report-output">Waiting for a completed task.</pre>
            </div>
            <div class="output-block">
              <h3>Task Snapshot</h3>
              <pre id="task-output">No task loaded.</pre>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h2>Execution Trace</h2>
          </div>
          <div class="panel-body">
            <div class="output-block">
              <h3>Events</h3>
              <pre id="events-output">No events loaded.</pre>
            </div>
            <div class="output-block">
              <h3>Tool Logs</h3>
              <pre id="tool-logs-output">No tool logs loaded.</pre>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <h2>Fixed Eval Cases</h2>
          </div>
          <div class="panel-body eval-shell">
            <div id="eval-summary" class="summary-grid">
              <div class="summary-card">
                <div class="summary-label">Pass Rate</div>
                <div class="summary-value">-</div>
                <div class="summary-note">Run the fixed regression set to populate metrics.</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">Cases</div>
                <div class="summary-value">0</div>
                <div class="summary-note">Completed eval case count.</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">Trace</div>
                <div class="summary-value">-</div>
                <div class="summary-note">Average trace completeness.</div>
              </div>
              <div class="summary-card">
                <div class="summary-label">Report</div>
                <div class="summary-value">-</div>
                <div class="summary-note">Average report completeness.</div>
              </div>
            </div>
            <div class="output-block">
              <h3>Eval Results</h3>
              <pre id="eval-results-output">No fixed eval summary loaded.</pre>
            </div>
            <div class="output-block">
              <h3>Eval Case Coverage</h3>
              <pre id="eval-case-coverage-output">No fixed eval case coverage loaded.</pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const state = {
      fileId: null,
      taskId: null,
      polling: null,
    };

    const statusEl = document.getElementById("task-status");
    const reportEl = document.getElementById("report-output");
    const reportListEl = document.getElementById("report-list");
    const taskEl = document.getElementById("task-output");
    const taskSummaryEl = document.getElementById("task-summary");
    const providerPillEl = document.getElementById("provider-pill");
    const providerMetaEl = document.getElementById("provider-meta");
    const providerDiagEl = document.getElementById("provider-diag");
    const projectStatusPillEl = document.getElementById("project-status-pill");
    const projectStatusMetaEl = document.getElementById("project-status-meta");
    const sessionStorePillEl = document.getElementById("session-store-pill");
    const sessionStoreMetaEl = document.getElementById("session-store-meta");
    const sessionStoreOutputEl = document.getElementById("session-store-output");
    const latestTaskPillEl = document.getElementById("latest-task-pill");
    const latestTaskMetaEl = document.getElementById("latest-task-meta");
    const latestTaskArtifactsOutputEl = document.getElementById("latest_task_artifacts_output");
    const latestTaskEvalPillEl = document.getElementById("latest-task-eval-pill");
    const latestTaskEvalMetaEl = document.getElementById("latest-task-eval-meta");
    const latestTaskEvalOutputEl = document.getElementById("latest_task_eval_output");
    const latestTaskJudgementPillEl = document.getElementById("latest-task-judgement-pill");
    const latestTaskJudgementMetaEl = document.getElementById("latest-task-judgement-meta");
    const latestTaskJudgementOutputEl = document.getElementById("latest_task_judgement_output");
    const latestTaskProcessPillEl = document.getElementById("latest-task-process-pill");
    const latestTaskProcessMetaEl = document.getElementById("latest-task-process-meta");
    const latestTaskProcessOutputEl = document.getElementById("latest_task_process_output");
    const latestTaskReportPillEl = document.getElementById("latest-task-report-pill");
    const latestTaskReportMetaEl = document.getElementById("latest-task-report-meta");
    const latestTaskReportOutputEl = document.getElementById("latest_task_report_output");
    const latestTaskContextPillEl = document.getElementById("latest-task-context-pill");
    const latestTaskContextMetaEl = document.getElementById("latest-task-context-meta");
    const latestTaskContextOutputEl = document.getElementById("latest_task_context_output");
    const latestTaskSemanticsPillEl = document.getElementById("latest-task-semantics-pill");
    const latestTaskSemanticsMetaEl = document.getElementById("latest-task-semantics-meta");
    const latestTaskSemanticsOutputEl = document.getElementById("latest_task_semantics_output");
    const latestTaskToolsPillEl = document.getElementById("latest-task-tools-pill");
    const latestTaskToolsMetaEl = document.getElementById("latest-task-tools-meta");
    const latestTaskToolsOutputEl = document.getElementById("latest_task_tools_output");
    const latestTaskErrorsPillEl = document.getElementById("latest-task-errors-pill");
    const latestTaskErrorsMetaEl = document.getElementById("latest-task-errors-meta");
    const latestTaskErrorsOutputEl = document.getElementById("latest_task_errors_output");
    const projectStatusSummaryEl = document.getElementById("project-status-summary");
    const projectStatusOutputEl = document.getElementById("project-status-output");
    const evalSummaryEl = document.getElementById("eval-summary");
    const evalResultsEl = document.getElementById("eval-results-output");
    const evalCaseCoverageEl = document.getElementById("eval-case-coverage-output");
    const chartPreviewEl = document.getElementById("chart-preview");
    const eventsEl = document.getElementById("events-output");
    const toolLogsEl = document.getElementById("tool-logs-output");
    const fileInput = document.getElementById("file-input");
    const questionInput = document.getElementById("question-input");
    const loadSampleButton = document.getElementById("load-sample-button");
    const uploadButton = document.getElementById("upload-button");
    const runButton = document.getElementById("run-analysis-button");
    const refreshButton = document.getElementById("refresh-button");
    const providerStatusButton = document.getElementById("provider-status-button");
    const providerSmokeButton = document.getElementById("provider-smoke-button");
    const projectStatusButton = document.getElementById("project-status-button");
    const evalCasesButton = document.getElementById("eval-cases-button");

    function setStatus(message) {
      statusEl.textContent = message;
    }

    function stringify(value) {
      return JSON.stringify(value, null, 2);
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function renderTaskSummary(task) {
      const toolCount = (task.tool_results || []).filter((item) => item.success).length;
      const overallScore = task.eval_result && typeof task.eval_result.overall_score !== "undefined"
        ? task.eval_result.overall_score
        : "-";
      taskSummaryEl.innerHTML = `
        <div class="summary-card">
          <div class="summary-label">Task</div>
          <div class="summary-value">${escapeHtml(task.task_id || "Unknown")}</div>
          <div class="summary-note">${escapeHtml(task.analysis_goal || "No analysis goal")}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Status</div>
          <div class="summary-value">${escapeHtml(task.status || "unknown")}</div>
          <div class="summary-note">${escapeHtml(task.current_step || "No current step")}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Tools</div>
          <div class="summary-value">${toolCount}</div>
          <div class="summary-note">${(task.chart_specs || []).length} chart specs recorded</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Score</div>
          <div class="summary-value">${escapeHtml(overallScore)}</div>
          <div class="summary-note">${escapeHtml((task.llm_judgement || {}).supported_by_tools === true ? "LLM judged as supported" : "LLM judgement pending or mixed")}</div>
        </div>
      `;
    }

    function renderReportHighlights(report) {
      const findings = report && Array.isArray(report.key_findings) ? report.key_findings : [];
      if (!findings.length) {
        reportListEl.innerHTML = "<li>No report findings yet.</li>";
        return;
      }
      reportListEl.innerHTML = findings.map((item) => `
        <li>
          <strong>${escapeHtml(item.finding || "Finding")}</strong><br>
          <span>${escapeHtml(item.evidence || "No evidence")}</span><br>
          <span class="fine">Source: ${escapeHtml(item.source_tool || "unknown")}</span>
        </li>
      `).join("");
    }

    function renderChartPreview(chartSpecs) {
      const chartSpec = Array.isArray(chartSpecs) && chartSpecs.length ? chartSpecs[0] : null;
      if (!chartSpec || !chartSpec.plotly_spec || !Array.isArray(chartSpec.plotly_spec.data) || !chartSpec.plotly_spec.data.length) {
        chartPreviewEl.innerHTML = `
          <div class="chart-meta">
            <span>Chart preview uses the persisted `chart_specs` output.</span>
          </div>
          <div id="chart-empty-state" class="chart-empty">No chart is available until a completed task returns chart specs.</div>
        `;
        return;
      }

      const trace = chartSpec.plotly_spec.data[0] || {};
      const xs = Array.isArray(trace.x) ? trace.x : [];
      const ys = Array.isArray(trace.y) ? trace.y.map((value) => Number(value) || 0) : [];
      const maxY = ys.length ? Math.max(...ys, 1) : 1;
      const width = 520;
      const height = 180;
      const leftPad = 26;
      const baseY = 146;
      const usableHeight = 110;

      let graphic = "";
      if (chartSpec.chart_type === "line") {
        const step = xs.length > 1 ? (width - 70) / (xs.length - 1) : 0;
        const points = ys.map((value, index) => {
          const x = 24 + index * step;
          const y = baseY - (value / maxY) * usableHeight;
          return { x, y, label: xs[index], value };
        });
        const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
        graphic = `
          <svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Line chart preview">
            <line x1="${leftPad}" y1="${baseY}" x2="${width - 18}" y2="${baseY}" stroke="#d8ccb8" />
            <path class="chart-line" d="${path}"></path>
            ${points.map((point) => `
              <circle class="chart-point" cx="${point.x}" cy="${point.y}" r="4"></circle>
              <text class="chart-label" x="${point.x}" y="${baseY + 16}" text-anchor="middle">${escapeHtml(point.label)}</text>
              <text class="chart-value" x="${point.x}" y="${point.y - 8}" text-anchor="middle">${escapeHtml(point.value)}</text>
            `).join("")}
          </svg>
        `;
      } else {
        const barWidth = xs.length ? Math.max(24, Math.min(64, (width - 80) / xs.length - 12)) : 36;
        const gap = xs.length ? ((width - 70) - barWidth * xs.length) / Math.max(xs.length - 1, 1) : 10;
        graphic = `
          <svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="Bar chart preview">
            <line x1="${leftPad}" y1="${baseY}" x2="${width - 18}" y2="${baseY}" stroke="#d8ccb8" />
            ${ys.map((value, index) => {
              const x = 28 + index * (barWidth + gap);
              const barHeight = (value / maxY) * usableHeight;
              const y = baseY - barHeight;
              return `
                <rect class="chart-bar" x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="6"></rect>
                <text class="chart-label" x="${x + barWidth / 2}" y="${baseY + 16}" text-anchor="middle">${escapeHtml(xs[index])}</text>
                <text class="chart-value" x="${x + barWidth / 2}" y="${y - 8}" text-anchor="middle">${escapeHtml(value)}</text>
              `;
            }).join("")}
          </svg>
        `;
      }

      chartPreviewEl.innerHTML = `
        <div class="chart-meta">
          <span>Type: ${escapeHtml(chartSpec.chart_type || "unknown")}</span>
          <span>Metric label: ${escapeHtml(chartSpec.metric_label || "n/a")}</span>
        </div>
        ${graphic}
      `;
    }

    function renderProviderStatus(status) {
      if (!status) {
        providerPillEl.textContent = "Not loaded";
        providerMetaEl.textContent = "Provider diagnostics will appear here.";
        providerDiagEl.textContent = "No provider status loaded yet.";
        return;
      }

      const pillLabel = status.diagnostics?.smoke_ready
        ? "Smoke ready"
        : (status.diagnostics?.provider_supported ? "Needs attention" : "Unsupported");
      providerPillEl.textContent = pillLabel;
      providerMetaEl.textContent = [
        `Provider: ${status.provider}`,
        `Key source: ${status.api_key_source || "missing"}`,
        `Base URL: ${status.base_url}`,
        `Model: ${status.model}`,
      ].join(" | ");
      const diag = status.diagnostics || {};
      const lines = [
        `provider_supported: ${diag.provider_supported}`,
        `key_source_kind: ${diag.key_source_kind}`,
        `smoke_ready: ${diag.smoke_ready}`,
      ];
      if (Array.isArray(diag.warnings) && diag.warnings.length) {
        lines.push(`warnings: ${diag.warnings.join(" ; ")}`);
      }
      if (Array.isArray(diag.recommendations) && diag.recommendations.length) {
        lines.push(`recommendations: ${diag.recommendations.join(" ; ")}`);
      }
      providerDiagEl.textContent = lines.join("\n");
    }

    function renderEvalSummary(summary) {
      if (!summary) {
        evalSummaryEl.innerHTML = `
          <div class="summary-card">
            <div class="summary-label">Pass Rate</div>
            <div class="summary-value">-</div>
            <div class="summary-note">Run the fixed regression set to populate metrics.</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Cases</div>
            <div class="summary-value">0</div>
            <div class="summary-note">Completed eval case count.</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Trace</div>
            <div class="summary-value">-</div>
            <div class="summary-note">Average trace completeness.</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Report</div>
            <div class="summary-value">-</div>
            <div class="summary-note">Average report completeness.</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Retries</div>
            <div class="summary-value">0</div>
            <div class="summary-note">retried_tool_calls / retry_attempts_total.</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Latency</div>
            <div class="summary-value">-</div>
            <div class="summary-note">average_tool_elapsed_ms_total.</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Chart</div>
            <div class="summary-value">-</div>
            <div class="summary-note">average_chart_validity.</div>
          </div>
          <div class="summary-card">
            <div class="summary-label">Field</div>
            <div class="summary-value">-</div>
            <div class="summary-note">average_field_validity.</div>
          </div>
        `;
        evalCaseCoverageEl.textContent = "No fixed eval case coverage loaded.";
        return;
      }

      evalSummaryEl.innerHTML = `
        <div class="summary-card">
          <div class="summary-label">Pass Rate</div>
          <div class="summary-value">${escapeHtml(summary.pass_rate)}</div>
          <div class="summary-note">${escapeHtml(summary.passed_cases)} passed / ${escapeHtml(summary.total_cases)} total</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Cases</div>
          <div class="summary-value">${escapeHtml(summary.total_cases)}</div>
          <div class="summary-note">${escapeHtml(summary.failed_cases)} failed</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Trace</div>
          <div class="summary-value">${escapeHtml(summary.average_trace_completeness)}</div>
          <div class="summary-note">Average trace completeness</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Report</div>
          <div class="summary-value">${escapeHtml(summary.average_report_completeness)}</div>
          <div class="summary-note">Average report completeness</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Retries</div>
          <div class="summary-value">${escapeHtml(summary.retried_tool_calls ?? 0)}</div>
          <div class="summary-note">${escapeHtml(summary.retry_attempts_total ?? 0)} total retry attempts</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Latency</div>
          <div class="summary-value">${escapeHtml(summary.average_tool_elapsed_ms_total ?? 0)}</div>
          <div class="summary-note">average_tool_elapsed_ms_total</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Chart</div>
          <div class="summary-value">${escapeHtml(summary.average_chart_validity ?? "none")}</div>
          <div class="summary-note">average_chart_validity</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Field</div>
          <div class="summary-value">${escapeHtml(summary.average_field_validity ?? "none")}</div>
          <div class="summary-note">average_field_validity</div>
        </div>
      `;

      const coveredCases = Array.isArray(summary.results) ? summary.results : [];
      evalCaseCoverageEl.textContent = coveredCases.length
        ? coveredCases.map((item) => `${item.case_id}: ${item.question}`).join("\n")
        : "No fixed eval case coverage loaded.";
    }

    function renderProjectStatus(payload) {
      if (!payload || !payload.summary) {
        projectStatusPillEl.textContent = "Not loaded";
        projectStatusMetaEl.textContent = "Runtime summary will appear here.";
        sessionStorePillEl.textContent = "Not loaded";
        sessionStoreMetaEl.textContent = "Redis-first / SQLite-fallback summary will appear here.";
        sessionStoreOutputEl.textContent = "No session store runtime summary loaded yet.";
        latestTaskPillEl.textContent = "Not loaded";
        latestTaskMetaEl.textContent = "Latest persisted task artifact coverage will appear here.";
        latestTaskArtifactsOutputEl.textContent = "No latest task artifact summary loaded yet.";
        latestTaskEvalPillEl.textContent = "Not loaded";
        latestTaskEvalMetaEl.textContent = "Latest persisted eval_result summary will appear here.";
        latestTaskEvalOutputEl.textContent = "No latest task evaluation summary loaded yet.";
        latestTaskJudgementPillEl.textContent = "Not loaded";
        latestTaskJudgementMetaEl.textContent = "Latest supplementary llm_judgement summary will appear here.";
        latestTaskJudgementOutputEl.textContent = "No latest task judgement summary loaded yet.";
        latestTaskProcessPillEl.textContent = "Not loaded";
        latestTaskProcessMetaEl.textContent = "Latest task trace and state summary will appear here.";
        latestTaskProcessOutputEl.textContent = "No latest task process summary loaded yet.";
        latestTaskReportPillEl.textContent = "Not loaded";
        latestTaskReportMetaEl.textContent = "Latest report richness summary will appear here.";
        latestTaskReportOutputEl.textContent = "No latest task report summary loaded yet.";
        latestTaskContextPillEl.textContent = "Not loaded";
        latestTaskContextMetaEl.textContent = "Latest RAG and checkpoint summary will appear here.";
        latestTaskContextOutputEl.textContent = "No latest task context summary loaded yet.";
        latestTaskSemanticsPillEl.textContent = "Not loaded";
        latestTaskSemanticsMetaEl.textContent = "Latest task goal and planning summary will appear here.";
        latestTaskSemanticsOutputEl.textContent = "No latest task semantics summary loaded yet.";
        latestTaskToolsPillEl.textContent = "Not loaded";
        latestTaskToolsMetaEl.textContent = "Latest tool execution summary will appear here.";
        latestTaskToolsOutputEl.textContent = "No latest task tool summary loaded yet.";
        latestTaskErrorsPillEl.textContent = "Not loaded";
        latestTaskErrorsMetaEl.textContent = "Latest failure and degradation summary will appear here.";
        latestTaskErrorsOutputEl.textContent = "No latest task error summary loaded yet.";
        projectStatusOutputEl.textContent = "No project runtime overview loaded yet.";
        return;
      }

      const summary = payload.summary;
      const tables = (summary.database || {}).tables || {};
      const provider = summary.provider || {};
      const providerDiagnostics = provider.diagnostics || {};
      const sessionStore = summary.session_store || {};
      const sessionStoreEvents = sessionStore.event_summary || {};
      const latestTask = summary.latest_task || null;
      const latestTaskArtifacts = latestTask ? (latestTask.artifacts || {}) : {};
      const latestTaskEvaluation = latestTask ? (latestTask.evaluation || {}) : {};
      const latestTaskJudgement = latestTask ? (latestTask.judgement || {}) : {};
      const latestTaskProcess = latestTask ? (latestTask.process || {}) : {};
      const latestTaskReport = latestTask ? (latestTask.report || {}) : {};
      const latestTaskContext = latestTask ? (latestTask.context || {}) : {};
      const latestTaskSemantics = latestTask ? (latestTask.semantics || {}) : {};
      const latestTaskTools = latestTask ? (latestTask.tools || {}) : {};
      const latestTaskErrors = latestTask ? (latestTask.errors || {}) : {};
      const files = tables.files || { exists: false, row_count: 0 };
      const tasks = tables.analysis_tasks || { exists: false, row_count: 0 };
      const events = tables.analysis_events || { exists: false, row_count: 0 };
      const toolLogs = tables.tool_call_logs || { exists: false, row_count: 0 };
      const evalResults = tables.eval_results || { exists: false, row_count: 0 };
      const demo = summary.demo || { available: false, path: "/demo" };

      projectStatusPillEl.textContent = demo.available ? "Demo ready" : "Needs attention";
      projectStatusMetaEl.textContent = [
        `Demo path: ${demo.path || "/demo"}`,
        `Provider: ${provider.provider || "unknown"}`,
        `Smoke ready: ${providerDiagnostics.smoke_ready}`,
      ].join(" | ");
      sessionStorePillEl.textContent = sessionStore.degraded_to_sqlite ? "SQLite fallback" : "Redis active";
      sessionStoreMetaEl.textContent = [
        `Preferred: ${sessionStore.preferred_backend || "redis"}`,
        `Active: ${sessionStore.active_backend || "unknown"}`,
        `Redis available: ${sessionStore.redis_available}`,
      ].join(" | ");
      sessionStoreOutputEl.textContent = [
        `preferred_backend: ${sessionStore.preferred_backend || "redis"}`,
        `active_backend: ${sessionStore.active_backend || "unknown"}`,
        `redis_available: ${sessionStore.redis_available}`,
        `degraded_to_sqlite: ${sessionStore.degraded_to_sqlite}`,
        `redis_url: ${sessionStore.redis_url || "unknown"}`,
        `warning_count: ${sessionStoreEvents.warning_count ?? 0}`,
        `recovered_count: ${sessionStoreEvents.recovered_count ?? 0}`,
        `latest_warning_task_id: ${sessionStoreEvents.latest_warning_task_id || "none"}`,
        `latest_recovered_task_id: ${sessionStoreEvents.latest_recovered_task_id || "none"}`,
        `latest_recovered_recovery_source: ${sessionStoreEvents.latest_recovered_recovery_source || "none"}`,
        `latest_recovered_segment_count: ${sessionStoreEvents.latest_recovered_segment_count ?? 0}`,
        `latest_recovered_segments: ${Array.isArray(sessionStoreEvents.latest_recovered_segments) ? sessionStoreEvents.latest_recovered_segments.join(", ") || "none" : "none"}`,
      ].join("\n");
      latestTaskPillEl.textContent = latestTask ? (latestTask.status || "available") : "No tasks";
      latestTaskMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `updated_at: ${latestTask.updated_at}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskArtifactsOutputEl.textContent = latestTask ? [
        `has_business_context: ${latestTaskArtifacts.has_business_context}`,
        `has_context_checkpoint: ${latestTaskArtifacts.has_context_checkpoint}`,
        `has_draft_report: ${latestTaskArtifacts.has_draft_report}`,
        `has_final_report: ${latestTaskArtifacts.has_final_report}`,
        `has_llm_judgement: ${latestTaskArtifacts.has_llm_judgement}`,
        `tool_call_log_count: ${latestTaskArtifacts.tool_call_log_count}`,
      ].join("\n") : "No latest task artifact summary loaded yet.";
      latestTaskEvalPillEl.textContent = latestTaskEvaluation.has_eval_result ? "Eval ready" : "No eval";
      latestTaskEvalMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `status: ${latestTask.status || "unknown"}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskEvalOutputEl.textContent = latestTask ? [
        `has_eval_result: ${latestTaskEvaluation.has_eval_result}`,
        `overall_score: ${latestTaskEvaluation.overall_score ?? "none"}`,
        `issue_count: ${latestTaskEvaluation.issue_count ?? 0}`,
        `suggestion_count: ${latestTaskEvaluation.suggestion_count ?? 0}`,
        `has_dimension_scores: ${latestTaskEvaluation.has_dimension_scores}`,
        `schema_valid: ${latestTaskEvaluation.schema_valid ?? false}`,
        `tool_success_rate: ${latestTaskEvaluation.tool_success_rate ?? "none"}`,
        `tool_elapsed_ms_total: ${latestTaskEvaluation.tool_elapsed_ms_total ?? 0}`,
        `field_validity: ${latestTaskEvaluation.field_validity ?? false}`,
        `chart_validity: ${latestTaskEvaluation.chart_validity ?? false}`,
        `report_completeness: ${latestTaskEvaluation.report_completeness ?? "none"}`,
        `trace_completeness: ${latestTaskEvaluation.trace_completeness ?? "none"}`,
      ].join("\n") : "No latest task evaluation summary loaded yet.";
      latestTaskJudgementPillEl.textContent = latestTask ? "Judgement ready" : "No tasks";
      latestTaskJudgementMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `supported_by_tools: ${latestTaskJudgement.supported_by_tools}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskJudgementOutputEl.textContent = latestTask ? [
        `supported_by_tools: ${latestTaskJudgement.supported_by_tools ?? false}`,
        `has_findings: ${latestTaskJudgement.has_findings ?? false}`,
        `issue_count: ${latestTaskJudgement.issue_count ?? 0}`,
      ].join("\n") : "No latest task judgement summary loaded yet.";
      latestTaskProcessPillEl.textContent = latestTask ? "Trace ready" : "No tasks";
      latestTaskProcessMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `latest_event_at: ${latestTaskProcess.latest_event_at || "none"}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskProcessOutputEl.textContent = latestTask ? [
        `pending_metric_count: ${latestTaskProcess.pending_metric_count ?? 0}`,
        `planned_tool_call_count: ${latestTaskProcess.planned_tool_call_count ?? 0}`,
        `event_count: ${latestTaskProcess.event_count ?? 0}`,
        `latest_event_type: ${latestTaskProcess.latest_event_type || "none"}`,
        `llm_issue_count: ${latestTaskProcess.llm_issue_count ?? 0}`,
        `route_decision_count: ${latestTaskProcess.route_decision_count ?? 0}`,
        `continued_route_decision_count: ${latestTaskProcess.continued_route_decision_count ?? 0}`,
        `finished_route_decision_count: ${latestTaskProcess.finished_route_decision_count ?? 0}`,
        `latest_route_decision: ${latestTaskProcess.latest_route_decision || "none"}`,
      ].join("\n") : "No latest task process summary loaded yet.";
      latestTaskReportPillEl.textContent = latestTask ? "Report ready" : "No tasks";
      latestTaskReportMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `status: ${latestTask.status || "unknown"}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskReportOutputEl.textContent = latestTask ? [
        `chart_spec_count: ${latestTaskReport.chart_spec_count ?? 0}`,
        `key_finding_count: ${latestTaskReport.key_finding_count ?? 0}`,
        `top_key_finding: ${latestTaskReport.top_key_finding || "none"}`,
        `business_suggestion_count: ${latestTaskReport.business_suggestion_count ?? 0}`,
        `data_limitation_count: ${latestTaskReport.data_limitation_count ?? 0}`,
        `next_step_count: ${latestTaskReport.next_step_count ?? 0}`,
      ].join("\n") : "No latest task report summary loaded yet.";
      latestTaskContextPillEl.textContent = latestTask ? "Context ready" : "No tasks";
      latestTaskContextMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `checkpoint_step: ${latestTaskContext.checkpoint_current_step || "none"}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskContextOutputEl.textContent = latestTask ? [
        `business_context_count: ${latestTaskContext.business_context_count ?? 0}`,
        `top_business_context_title: ${latestTaskContext.top_business_context_title || "none"}`,
        `top_business_context_score: ${latestTaskContext.top_business_context_score ?? "none"}`,
        `top_business_context_related_field_count: ${latestTaskContext.top_business_context_related_field_count ?? 0}`,
        `top_business_context_has_score_breakdown: ${latestTaskContext.top_business_context_has_score_breakdown ?? false}`,
        `top_business_context_keyword_score: ${latestTaskContext.top_business_context_keyword_score ?? "none"}`,
        `top_business_context_field_score: ${latestTaskContext.top_business_context_field_score ?? "none"}`,
        `top_business_context_phrase_score: ${latestTaskContext.top_business_context_phrase_score ?? "none"}`,
        `top_business_context_bm25_score: ${latestTaskContext.top_business_context_bm25_score ?? "none"}`,
        `checkpoint_current_step: ${latestTaskContext.checkpoint_current_step || "none"}`,
        `checkpoint_status: ${latestTaskContext.checkpoint_status || "none"}`,
        `checkpoint_pending_metric_count: ${latestTaskContext.checkpoint_pending_metric_count ?? 0}`,
        `checkpoint_finding_count: ${latestTaskContext.checkpoint_finding_count ?? 0}`,
        `checkpoint_business_context_title_count: ${latestTaskContext.checkpoint_business_context_title_count ?? 0}`,
        `checkpoint_business_context_titles: ${Array.isArray(latestTaskContext.checkpoint_business_context_titles) ? latestTaskContext.checkpoint_business_context_titles.join(", ") || "none" : "none"}`,
        `checkpoint_draft_report_status: ${latestTaskContext.checkpoint_draft_report_status || "none"}`,
        `checkpoint_latest_error_code: ${latestTaskContext.checkpoint_latest_error_code || "none"}`,
      ].join("\n") : "No latest task context summary loaded yet.";
      latestTaskSemanticsPillEl.textContent = latestTask ? "Planning ready" : "No tasks";
      latestTaskSemanticsMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `current_step: ${latestTaskSemantics.current_step || "none"}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskSemanticsOutputEl.textContent = latestTask ? [
        `analysis_goal: ${latestTaskSemantics.analysis_goal || "none"}`,
        `analysis_plan_count: ${latestTaskSemantics.analysis_plan_count ?? 0}`,
        `current_step: ${latestTaskSemantics.current_step || "none"}`,
        `completed_step_count: ${latestTaskSemantics.completed_step_count ?? 0}`,
        `finding_count: ${latestTaskSemantics.finding_count ?? 0}`,
        `latest_finding_summary: ${latestTaskSemantics.latest_finding_summary || "none"}`,
        `dimension_field: ${latestTaskSemantics.dimension_field || "none"}`,
        `match_analysis_type: ${latestTaskSemantics.match_analysis_type || "none"}`,
        `candidate_field_count: ${latestTaskSemantics.candidate_field_count ?? 0}`,
        `match_warning_count: ${latestTaskSemantics.match_warning_count ?? 0}`,
        `planned_tool_sequence: ${Array.isArray(latestTaskSemantics.planned_tool_sequence) ? latestTaskSemantics.planned_tool_sequence.join(", ") || "none" : "none"}`,
        `metric_count: ${latestTaskSemantics.metric_count ?? 0}`,
      ].join("\n") : "No latest task semantics summary loaded yet.";
      latestTaskToolsPillEl.textContent = latestTask ? "Tools ready" : "No tasks";
      latestTaskToolsMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `latest_tool_name: ${latestTaskTools.latest_tool_name || "none"}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskToolsOutputEl.textContent = latestTask ? [
        `tool_result_count: ${latestTaskTools.tool_result_count ?? 0}`,
        `successful_tool_result_count: ${latestTaskTools.successful_tool_result_count ?? 0}`,
        `failed_tool_result_count: ${latestTaskTools.failed_tool_result_count ?? 0}`,
        `total_tool_elapsed_ms: ${latestTaskTools.total_tool_elapsed_ms ?? 0}`,
        `retried_tool_result_count: ${latestTaskTools.retried_tool_result_count ?? 0}`,
        `retry_attempts_total: ${latestTaskTools.retry_attempts_total ?? 0}`,
        `latest_retry_status: ${latestTaskTools.latest_retry_status || "none"}`,
        `latest_tool_name: ${latestTaskTools.latest_tool_name || "none"}`,
      ].join("\n") : "No latest task tool summary loaded yet.";
      latestTaskErrorsPillEl.textContent = latestTask
        ? (latestTaskErrors.error_count > 0 ? "Errors visible" : "No errors")
        : "No tasks";
      latestTaskErrorsMetaEl.textContent = latestTask
        ? [`task_id: ${latestTask.task_id}`, `latest_error_code: ${latestTaskErrors.latest_error_code || "none"}`].join(" | ")
        : "No persisted task found yet.";
      latestTaskErrorsOutputEl.textContent = latestTask ? [
        `error_count: ${latestTaskErrors.error_count ?? 0}`,
        `latest_error_code: ${latestTaskErrors.latest_error_code || "none"}`,
        `latest_error_message: ${latestTaskErrors.latest_error_message || "none"}`,
        `has_degradation: ${latestTaskErrors.has_degradation ?? false}`,
      ].join("\n") : "No latest task error summary loaded yet.";

      projectStatusSummaryEl.innerHTML = `
        <div class="summary-card">
          <div class="summary-label">Demo</div>
          <div class="summary-value">${escapeHtml(demo.available ? "Ready" : "Off")}</div>
          <div class="summary-note">${escapeHtml(demo.path || "/demo")}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Files</div>
          <div class="summary-value">${escapeHtml(files.row_count)}</div>
          <div class="summary-note">${escapeHtml(files.exists ? "SQLite table present" : "SQLite table missing")}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Tasks</div>
          <div class="summary-value">${escapeHtml(tasks.row_count)}</div>
          <div class="summary-note">${escapeHtml(tasks.exists ? "Persisted analysis rows" : "SQLite table missing")}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">Events</div>
          <div class="summary-value">${escapeHtml(events.row_count)}</div>
          <div class="summary-note">${escapeHtml(events.exists ? "Persisted event rows" : "SQLite table missing")}</div>
        </div>
      `;

      projectStatusOutputEl.textContent = [
        `provider: ${provider.provider || "unknown"}`,
        `api_key_source: ${provider.api_key_source || "missing"}`,
        `files: exists=${files.exists} row_count=${files.row_count}`,
        `analysis_tasks: exists=${tasks.exists} row_count=${tasks.row_count}`,
        `analysis_events: exists=${events.exists} row_count=${events.row_count}`,
        `tool_call_logs: exists=${toolLogs.exists} row_count=${toolLogs.row_count}`,
        `eval_results: exists=${evalResults.exists} row_count=${evalResults.row_count}`,
      ].join("\n");
    }

    async function apiFetch(url, options = {}) {
      const response = await fetch(url, options);
      const contentType = response.headers.get("content-type") || "";
      const payload = contentType.includes("application/json")
        ? await response.json()
        : await response.text();
      if (!response.ok) {
        const detail = typeof payload === "string" ? payload : (payload.detail || stringify(payload));
        throw new Error(detail);
      }
      return payload;
    }

    async function uploadFile() {
      if (!fileInput.files.length) {
        throw new Error("Please choose a CSV or Excel file first.");
      }
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);
      setStatus("Uploading file and building profile...");
      const profile = await apiFetch("/api/files/upload", {
        method: "POST",
        body: formData,
      });
      state.fileId = profile.file_id;
      taskEl.textContent = stringify({ file_profile: profile });
      setStatus("File uploaded. File ID: " + profile.file_id);
      return profile;
    }

    async function loadBuiltInSample() {
      setStatus("Loading built-in sample data...");
      const profile = await apiFetch("/api/files/upload-sample", {
        method: "POST",
      });
      state.fileId = profile.file_id;
      taskEl.textContent = stringify({ file_profile: profile });
      setStatus("Built-in sample loaded. File ID: " + profile.file_id);
      return profile;
    }

    async function loadTaskArtifacts(taskId) {
      const [task, events, toolLogs] = await Promise.all([
        apiFetch(`/api/analysis/${taskId}`),
        apiFetch(`/api/analysis/${taskId}/events`),
        apiFetch(`/api/analysis/${taskId}/tool-logs`),
      ]);

      taskEl.textContent = stringify({
        task_id: task.task_id,
        status: task.status,
        analysis_goal: task.analysis_goal,
        analysis_plan: task.analysis_plan,
        eval_result: task.eval_result,
        llm_judgement: task.llm_judgement,
      });
      reportEl.textContent = stringify(task.final_report || {});
      renderTaskSummary(task);
      renderReportHighlights(task.final_report || {});
      renderChartPreview(task.chart_specs || []);
      eventsEl.textContent = stringify(events.events || []);
      toolLogsEl.textContent = stringify(toolLogs.tool_call_logs || []);
      setStatus(`Task ${task.task_id} status: ${task.status}`);
      return task;
    }

    async function loadProviderStatus() {
      setStatus("Loading provider status...");
      const payload = await apiFetch("/api/llm/provider-status");
      renderProviderStatus(payload);
      setStatus(`Provider status loaded: ${payload.provider}`);
      return payload;
    }

    async function runProviderSmoke() {
      setStatus("Running provider smoke...");
      const payload = await apiFetch("/api/llm/provider-smoke", { method: "POST" });
      renderProviderStatus(payload.provider_resolution);
      providerDiagEl.textContent = [
        providerDiagEl.textContent,
        "",
        `Smoke ok: ${payload.ok}`,
        payload.error_message ? `Smoke error: ${payload.error_message}` : `Analysis goal: ${payload.analysis_goal}`,
      ].join("\n");
      setStatus(payload.ok ? "Provider smoke succeeded." : `Provider smoke failed: ${payload.error_message}`);
      return payload;
    }

    async function runEvalCases() {
      setStatus("Running fixed eval cases...");
      const payload = await apiFetch("/api/eval/cases/run", { method: "POST" });
      renderEvalSummary(payload);
      evalResultsEl.textContent = stringify(payload);
      setStatus(`Fixed eval cases completed: ${payload.passed_cases}/${payload.total_cases} passed.`);
      return payload;
    }

    async function loadProjectStatus() {
      setStatus("Loading project runtime overview...");
      const payload = await apiFetch("/api/project-status");
      renderProjectStatus(payload);
      setStatus("Project runtime overview loaded.");
      return payload;
    }

    async function startAndRunAnalysis() {
      if (!state.fileId) {
        await uploadFile();
      }
      const question = questionInput.value.trim();
      if (!question) {
        throw new Error("Please enter an analysis question.");
      }

      setStatus("Creating analysis task...");
      const startPayload = await apiFetch("/api/analysis/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: state.fileId, question }),
      });
      state.taskId = startPayload.task_id;

      taskEl.textContent = stringify(startPayload);
      setStatus(`Task created: ${state.taskId}. Running analysis...`);

      const runPayload = await apiFetch(`/api/analysis/${state.taskId}/run`, {
        method: "POST",
      });

      reportEl.textContent = stringify(runPayload.final_report || {});
      taskEl.textContent = stringify({
        task_id: runPayload.task_id,
        status: runPayload.status,
        analysis_goal: runPayload.analysis_goal,
        analysis_plan: runPayload.analysis_plan,
        eval_result: runPayload.eval_result,
      });
      renderTaskSummary(runPayload);
      renderReportHighlights(runPayload.final_report || {});
      renderChartPreview(runPayload.chart_specs || []);

      await loadTaskArtifacts(state.taskId);
      startPolling();
    }

    function startPolling() {
      if (!state.taskId) {
        return;
      }
      if (state.polling) {
        clearInterval(state.polling);
      }
      state.polling = setInterval(async () => {
        try {
          const task = await loadTaskArtifacts(state.taskId);
          if (task.status !== "running") {
            clearInterval(state.polling);
            state.polling = null;
          }
        } catch (error) {
          clearInterval(state.polling);
          state.polling = null;
          setStatus("Polling stopped: " + error.message);
        }
      }, 3000);
    }

    uploadButton.addEventListener("click", async () => {
      uploadButton.disabled = true;
      try {
        await uploadFile();
      } catch (error) {
        setStatus("Upload failed: " + error.message);
      } finally {
        uploadButton.disabled = false;
      }
    });

    loadSampleButton.addEventListener("click", async () => {
      loadSampleButton.disabled = true;
      try {
        await loadBuiltInSample();
      } catch (error) {
        setStatus("Loading sample failed: " + error.message);
      } finally {
        loadSampleButton.disabled = false;
      }
    });

    runButton.addEventListener("click", async () => {
      runButton.disabled = true;
      try {
        await startAndRunAnalysis();
      } catch (error) {
        setStatus("Analysis failed: " + error.message);
      } finally {
        runButton.disabled = false;
      }
    });

    refreshButton.addEventListener("click", async () => {
      if (!state.taskId) {
        setStatus("No task is available to refresh.");
        return;
      }
      refreshButton.disabled = true;
      try {
        await loadTaskArtifacts(state.taskId);
      } catch (error) {
        setStatus("Refresh failed: " + error.message);
      } finally {
        refreshButton.disabled = false;
      }
    });

    providerStatusButton.addEventListener("click", async () => {
      providerStatusButton.disabled = true;
      try {
        await loadProviderStatus();
      } catch (error) {
        setStatus("Provider status failed: " + error.message);
      } finally {
        providerStatusButton.disabled = false;
      }
    });

    providerSmokeButton.addEventListener("click", async () => {
      providerSmokeButton.disabled = true;
      try {
        await runProviderSmoke();
      } catch (error) {
        setStatus("Provider smoke failed: " + error.message);
      } finally {
        providerSmokeButton.disabled = false;
      }
    });

    projectStatusButton.addEventListener("click", async () => {
      projectStatusButton.disabled = true;
      try {
        await loadProjectStatus();
      } catch (error) {
        setStatus("Project runtime overview failed: " + error.message);
      } finally {
        projectStatusButton.disabled = false;
      }
    });

    evalCasesButton.addEventListener("click", async () => {
      evalCasesButton.disabled = true;
      try {
        await runEvalCases();
      } catch (error) {
        setStatus("Fixed eval cases failed: " + error.message);
      } finally {
        evalCasesButton.disabled = false;
      }
    });

    document.querySelectorAll("[data-question]").forEach((button) => {
      button.addEventListener("click", () => {
        questionInput.value = button.dataset.question;
      });
    });

    loadProviderStatus().catch((error) => {
      setStatus("Initial provider status load failed: " + error.message);
    });

    loadProjectStatus().catch((error) => {
      setStatus("Initial project runtime overview load failed: " + error.message);
    });
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
