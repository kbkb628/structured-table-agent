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

    $uploadRaw = & curl.exe -s -X POST -F "file=@$samplePath" "$BaseUrl/api/files/upload"
    if (-not $uploadRaw) {
        throw "Upload request returned an empty response."
    }

    $upload = $uploadRaw | ConvertFrom-Json

    $questions = @(
        "analyse category sales top 5",
        "analyse sales by region",
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

    [pscustomobject]@{
        upload_file_id = $upload.file_id
        upload_rows = $upload.row_count
        upload_columns = $upload.column_count
        runs = $runs
        rerun_eval_task = $rerunEval.task_id
        rerun_eval_score = $rerunEval.eval_result.overall_score
    } | ConvertTo-Json -Depth 6
} finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force
    }
}
