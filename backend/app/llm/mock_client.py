from app.llm.base import LLMClient
from app.llm.prompt_templates import CATEGORY_TEMPLATE, CHANNEL_TEMPLATE, FALLBACK_TEMPLATE, REGION_TEMPLATE


class MockLLMClient(LLMClient):
    def _context_titles(self, business_context: list[dict]) -> list[str]:
        return [item["title"] for item in business_context if item.get("title")]

    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        del file_profile
        lowered = question.lower()
        titles = self._context_titles(business_context)
        context_note = f" Context: {', '.join(titles)}." if titles else ""

        if "category" in lowered and "sales" in lowered:
            return CATEGORY_TEMPLATE + context_note
        if "region" in lowered and "sales" in lowered:
            return REGION_TEMPLATE + context_note
        if "channel" in lowered and ("sales" in lowered or "order" in lowered):
            return CHANNEL_TEMPLATE + context_note
        return FALLBACK_TEMPLATE + context_note

    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
    ) -> list[str]:
        del file_profile
        del business_context
        lowered = analysis_goal.lower()
        if "category" in lowered:
            return [
                "identify the product category and sales amount fields",
                "aggregate sales amount by category",
                "sort the grouped result in descending order",
                "generate a comparison chart and summary",
            ]
        if "regional" in lowered or "region" in lowered:
            return [
                "identify the region and sales amount fields",
                "aggregate sales amount by region",
                "compare the grouped regional results",
                "generate a chart and business summary",
            ]
        if "channel" in lowered:
            return [
                "identify the channel, order id, and sales amount fields",
                "aggregate order count by channel",
                "aggregate sales amount by channel",
                "generate charts and compare channel performance",
            ]
        return [
            "identify the most relevant dimension and metric fields",
            "run grouped aggregation on the uploaded data",
            "review the grouped result and generate a chart",
            "produce a concise analysis summary",
        ]

    def generate_report(
        self,
        analysis_goal: str,
        intermediate_findings: list[dict],
        chart_specs: list[dict],
        business_context: list[dict],
    ) -> dict:
        context_titles = [item.get("title") for item in business_context if item.get("title")]
        summary = intermediate_findings[0]["summary"] if intermediate_findings else "No findings were available."
        return {
            "title": "MockLLM Structured Summary",
            "analysis_goal": analysis_goal,
            "key_findings": [
                {
                    "finding": summary,
                    "evidence": f"Context used: {', '.join(context_titles) or 'none'}.",
                    "source_tool": "mock_llm_report",
                }
            ],
            "chart_explanations": [
                f"Chart type included: {item.get('chart_type', 'unknown')}."
                for item in chart_specs
            ]
            or ["No chart context was available."],
            "business_suggestions": ["Validate the deterministic tool output before expanding the analysis scope."],
            "data_limitations": ["This mock report is used only as a replaceable LLM interface placeholder."],
            "next_steps": ["Keep the final persisted report grounded in tool outputs."],
        }

    def judge_report(self, question: str, final_report: dict, tool_results: list[dict]) -> dict:
        del question
        has_findings = bool(final_report.get("key_findings"))
        has_tool_rows = any(item.get("data", {}).get("rows") for item in tool_results)
        issues = []
        if not has_findings:
            issues.append("Report contains no key findings.")
        if not has_tool_rows:
            issues.append("No tool rows were available for judging.")
        return {
            "supported_by_tools": has_tool_rows,
            "has_findings": has_findings,
            "issue_count": len(issues),
            "issues": issues,
        }
