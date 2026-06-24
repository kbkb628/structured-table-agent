param(
    [string]$Question = "analyse sales by region"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$backendDir = Join-Path $repoRoot "backend"
$pythonPath = Join-Path $backendDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    throw "Python venv not found: $pythonPath"
}

$env:PYTHONPATH = "backend"
$env:LLM_PROVIDER = "qwen"

$questionJson = $Question | ConvertTo-Json -Compress

$code = @"
import json
from app.llm.factory import describe_llm_provider_resolution, get_llm_client

QUESTION = $questionJson

resolution = describe_llm_provider_resolution()
payload = {
    "provider_resolution": resolution,
}

try:
    client = get_llm_client()
    payload["client_type"] = type(client).__name__
    payload["analysis_goal"] = client.generate_analysis_goal(
        question=QUESTION,
        file_profile={
            "filename": "sales_orders.csv",
            "row_count": 10,
            "column_count": 3,
            "columns": [
                {"name": "region", "type": "string"},
                {"name": "sales_amount", "type": "number"},
                {"name": "order_id", "type": "string"},
            ],
        },
        business_context=[
            {"id": "metric_sales_amount", "title": "metric_sales_amount", "content": "sales_amount sum gives sales amount"},
            {"id": "dimension_region", "title": "dimension_region", "content": "region can be used for regional comparison"},
        ],
    )
    payload["ok"] = True
except Exception as exc:
    payload["ok"] = False
    payload["error_type"] = type(exc).__name__
    payload["error_message"] = str(exc)

print(json.dumps(payload, ensure_ascii=False, indent=2))
"@

@"
$code
"@ | & $pythonPath -
