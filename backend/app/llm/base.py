from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def generate_analysis_goal(
        self,
        question: str,
        file_profile: dict,
        business_context: list[dict],
        memory_context: dict,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
        memory_context: dict,
    ) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def generate_report(
        self,
        analysis_goal: str,
        intermediate_findings: list[dict],
        chart_specs: list[dict],
        business_context: list[dict],
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def judge_report(self, question: str, final_report: dict, tool_results: list[dict]) -> dict:
        raise NotImplementedError
