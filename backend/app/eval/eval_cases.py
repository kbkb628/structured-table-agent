import json
import uuid

from app.agent.graph import run_analysis_graph
from app.core.config import SAMPLE_DIR
from app.storage.analysis_store import record_event
from app.storage.analysis_store import create_task
from app.storage.file_store import save_file_record
from app.storage.models import FileRecord
from app.tools.data_profile import build_file_profile
from app.llm.mock_client import MockLLMClient
from app.rag.keyword_retriever import retrieve_business_context


def get_fixed_eval_cases() -> list[dict]:
    return [
        {
            "case_id": "category_topn",
            "question": "analyse category sales top 5",
            "expected_status": "completed",
            "min_tool_results": 1,
            "min_chart_specs": 1,
            "min_overall_score": 0.8,
        },
        {
            "case_id": "region_compare",
            "question": "analyse sales by region",
            "expected_status": "completed",
            "min_tool_results": 1,
            "min_chart_specs": 1,
            "min_overall_score": 0.8,
        },
        {
            "case_id": "channel_performance",
            "question": "analyse channel order count and sales performance",
            "expected_status": "completed",
            "min_tool_results": 2,
            "min_chart_specs": 2,
            "min_overall_score": 0.8,
        },
    ]


def _register_sample_file() -> dict:
    sample_path = SAMPLE_DIR / "sales_orders.csv"
    file_id = f"file_eval_{uuid.uuid4().hex[:12]}"
    created_at = "2026-06-17T00:00:00+00:00"
    profile = build_file_profile(
        sample_path,
        file_id=file_id,
        created_at=created_at,
        filename=sample_path.name,
    )
    save_file_record(
        FileRecord(
            file_id=profile.file_id,
            filename=profile.filename,
            stored_path=str(sample_path),
            row_count=profile.row_count,
            column_count=profile.column_count,
            columns_json=json.dumps([item.model_dump() for item in profile.columns], ensure_ascii=False),
            created_at=profile.created_at,
        )
    )
    return profile.model_dump()


def _build_case_task(case: dict, file_profile: dict) -> dict:
    question = case["question"]
    business_context = retrieve_business_context(question, file_profile)["items"]
    llm_client = MockLLMClient()
    analysis_goal = llm_client.generate_analysis_goal(question, file_profile, business_context)
    analysis_plan = llm_client.generate_analysis_plan(analysis_goal, file_profile, business_context)
    task_id = f"task_eval_{uuid.uuid4().hex[:12]}"

    state = {
        "task_id": task_id,
        "file_id": file_profile["file_id"],
        "question": question,
        "analysis_goal": analysis_goal,
        "file_profile": file_profile,
        "field_understanding": {},
        "business_context": business_context,
        "analysis_plan": analysis_plan,
        "current_step": "created",
        "completed_steps": [],
        "intermediate_findings": [],
        "tool_results": [],
        "chart_specs": [],
        "draft_report": {},
        "final_report": {},
        "eval_result": {},
        "events": [],
        "errors": [],
        "status": "created",
    }
    create_task(task_id, file_profile["file_id"], question, state)
    record_event(task_id, "task_created", "eval_cases", "task created", {"status": "created"})
    record_event(
        task_id,
        "rag_retrieved",
        "eval_cases",
        "business context retrieved",
        {"item_count": len(business_context), "item_ids": [item["id"] for item in business_context]},
    )
    record_event(
        task_id,
        "goal_understood",
        "eval_cases",
        "analysis goal generated",
        {"analysis_goal": analysis_goal},
    )
    record_event(
        task_id,
        "plan_generated",
        "eval_cases",
        "analysis plan generated",
        {"analysis_plan": analysis_plan},
    )
    return state


def _evaluate_case(case: dict, result: dict) -> dict:
    failures: list[str] = []
    if result["status"] != case["expected_status"]:
        failures.append(f"Expected status {case['expected_status']}, got {result['status']}.")
    if len(result["tool_results"]) < case["min_tool_results"]:
        failures.append(
            f"Expected at least {case['min_tool_results']} tool results, got {len(result['tool_results'])}."
        )
    if len(result["chart_specs"]) < case["min_chart_specs"]:
        failures.append(
            f"Expected at least {case['min_chart_specs']} chart specs, got {len(result['chart_specs'])}."
        )
    if result["eval_result"]["overall_score"] < case["min_overall_score"]:
        failures.append(
            f"Expected overall score >= {case['min_overall_score']}, got {result['eval_result']['overall_score']}."
        )

    return {
        "case_id": case["case_id"],
        "question": case["question"],
        "passed": len(failures) == 0,
        "task_id": result["task_id"],
        "status": result["status"],
        "overall_score": result["eval_result"]["overall_score"],
        "issues": result["eval_result"]["issues"],
        "assertion_failures": failures,
    }


def run_fixed_eval_cases() -> dict:
    file_profile = _register_sample_file()
    cases = get_fixed_eval_cases()
    results = []

    for case in cases:
        state = _build_case_task(case, file_profile)
        result = run_analysis_graph(state["task_id"])
        results.append(_evaluate_case(case, result))

    passed_cases = sum(1 for item in results if item["passed"])
    total_cases = len(results)
    failed_cases = total_cases - passed_cases

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "pass_rate": round(passed_cases / total_cases, 2) if total_cases else 0.0,
        "results": results,
    }
