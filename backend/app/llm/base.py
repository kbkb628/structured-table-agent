from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
    ) -> list[str]:
        raise NotImplementedError
