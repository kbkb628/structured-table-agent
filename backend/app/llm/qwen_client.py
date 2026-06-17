from app.llm.base import LLMClient


class QwenClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 30,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        del question
        del file_profile
        del business_context
        return "Qwen provider placeholder goal"

    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
    ) -> list[str]:
        del analysis_goal
        del file_profile
        del business_context
        return ["Qwen provider placeholder plan"]

    def generate_report(
        self,
        intermediate_findings: list[dict],
        chart_specs: list[dict],
        business_context: list[dict],
    ) -> dict:
        del intermediate_findings
        del chart_specs
        del business_context
        return {}

    def judge_report(self, question: str, final_report: dict, tool_results: list[dict]) -> dict:
        del question
        del final_report
        del tool_results
        return {}
