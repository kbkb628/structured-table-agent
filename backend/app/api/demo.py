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

          <label>
            Analysis Question
            <textarea id="question-input" placeholder="analyse sales by region">analyse sales by region</textarea>
          </label>

          <div class="chips">
            <button class="chip" type="button" data-question="analyse category sales top 5">TopN</button>
            <button class="chip" type="button" data-question="analyse category sales share">Share</button>
            <button class="chip" type="button" data-question="analyse category sales anomalies">Anomaly</button>
            <button class="chip" type="button" data-question="analyse sales trend by order date">Trend</button>
            <button class="chip" type="button" data-question="analyse channel order count and sales performance">Channel</button>
          </div>

          <div class="button-row">
            <button id="upload-button" class="secondary" type="button">1. Upload File</button>
            <button id="run-analysis-button" class="primary" type="button">2. Start And Run</button>
            <button id="refresh-button" class="ghost" type="button">Refresh Task</button>
          </div>

          <div id="task-status" class="status">No file uploaded yet.</div>
          <div class="hint">
            The page uses existing APIs only:
            <span class="fine">`/api/files/upload`, `/api/analysis/start`, `/api/analysis/{task_id}/run`, `/api/analysis/{task_id}`, `/events`, `/tool-logs`.</span>
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
    const taskEl = document.getElementById("task-output");
    const eventsEl = document.getElementById("events-output");
    const toolLogsEl = document.getElementById("tool-logs-output");
    const fileInput = document.getElementById("file-input");
    const questionInput = document.getElementById("question-input");
    const uploadButton = document.getElementById("upload-button");
    const runButton = document.getElementById("run-analysis-button");
    const refreshButton = document.getElementById("refresh-button");

    function setStatus(message) {
      statusEl.textContent = message;
    }

    function stringify(value) {
      return JSON.stringify(value, null, 2);
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
      eventsEl.textContent = stringify(events.events || []);
      toolLogsEl.textContent = stringify(toolLogs.tool_call_logs || []);
      setStatus(`Task ${task.task_id} status: ${task.status}`);
      return task;
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

    document.querySelectorAll("[data-question]").forEach((button) => {
      button.addEventListener("click", () => {
        questionInput.value = button.dataset.question;
      });
    });
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
