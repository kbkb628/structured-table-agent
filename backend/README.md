# Day 1 MVP Backend

## Scope

- CSV upload
- File profiling
- SQLite metadata persistence
- DuckDB groupby aggregation

## Setup with uv

```powershell
cd E:\bgagent1\backend
uv sync
uv run uvicorn app.main:app --reload
```

## pip alternative

```powershell
cd E:\bgagent1\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=120 fastapi uvicorn python-multipart pandas duckdb pytest httpx
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Tests

```powershell
cd E:\bgagent1\backend
.\.venv\Scripts\python.exe -m pytest
```
