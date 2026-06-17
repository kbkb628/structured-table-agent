import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.llm.base import LLMClient
from app.llm.prompt_templates import GOAL_SYSTEM_PROMPT, JUDGE_SYSTEM_PROMPT, PLAN_SYSTEM_PROMPT, REPORT_SYSTEM_PROMPT
from app.schemas.report_schema import FinalReport


class QwenResponseError(RuntimeError):
    pass


class QwenClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 30,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.endpoint = f"{self.base_url}/chat/completions"

    def _extract_message_content(self, response_payload: dict) -> str:
        try:
            content = response_payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise QwenResponseError("Qwen response did not contain a usable message content.") from exc

        if isinstance(content, list):
            text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
            content = "".join(text_parts)

        if not isinstance(content, str) or not content.strip():
            raise QwenResponseError("Qwen response content was empty.")
        return content

    def _post_json(self, payload: dict) -> dict:
        request = Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="ignore")
            raise QwenResponseError(f"Qwen HTTP error {exc.code}: {error_body}") from exc
        except URLError as exc:
            raise QwenResponseError(f"Qwen request failed: {exc.reason}") from exc

        try:
            return json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise QwenResponseError("Qwen returned a non-JSON HTTP response.") from exc

    def _chat_json(self, system_prompt: str, user_payload: dict) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        response_payload = self._post_json(payload)
        content = self._extract_message_content(response_payload)
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise QwenResponseError("Qwen message content was not valid JSON.") from exc

    def generate_analysis_goal(self, question: str, file_profile: dict, business_context: list[dict]) -> str:
        payload = self._chat_json(
            GOAL_SYSTEM_PROMPT,
            {
                "question": question,
                "file_profile": file_profile,
                "business_context": business_context,
            },
        )
        goal = payload.get("analysis_goal")
        if not isinstance(goal, str) or not goal.strip():
            raise QwenResponseError("Qwen did not return a valid analysis_goal.")
        return goal.strip()

    def generate_analysis_plan(
        self,
        analysis_goal: str,
        file_profile: dict,
        business_context: list[dict],
    ) -> list[str]:
        payload = self._chat_json(
            PLAN_SYSTEM_PROMPT,
            {
                "analysis_goal": analysis_goal,
                "file_profile": file_profile,
                "business_context": business_context,
            },
        )
        plan = payload.get("analysis_plan")
        if not isinstance(plan, list) or not all(isinstance(item, str) and item.strip() for item in plan):
            raise QwenResponseError("Qwen did not return a valid analysis_plan.")
        return [item.strip() for item in plan]

    def generate_report(
        self,
        analysis_goal: str,
        intermediate_findings: list[dict],
        chart_specs: list[dict],
        business_context: list[dict],
    ) -> dict:
        payload = self._chat_json(
            REPORT_SYSTEM_PROMPT,
            {
                "analysis_goal": analysis_goal,
                "intermediate_findings": intermediate_findings,
                "chart_specs": chart_specs,
                "business_context": business_context,
            },
        )
        return FinalReport.model_validate(payload).model_dump()

    def judge_report(self, question: str, final_report: dict, tool_results: list[dict]) -> dict:
        payload = self._chat_json(
            JUDGE_SYSTEM_PROMPT,
            {
                "question": question,
                "final_report": final_report,
                "tool_results": tool_results,
            },
        )
        supported_by_tools = payload.get("supported_by_tools")
        has_findings = payload.get("has_findings")
        issues = payload.get("issues", [])
        issue_count = payload.get("issue_count")
        if not isinstance(supported_by_tools, bool) or not isinstance(has_findings, bool):
            raise QwenResponseError("Qwen did not return valid judgement booleans.")
        if not isinstance(issues, list) or not all(isinstance(item, str) for item in issues):
            raise QwenResponseError("Qwen did not return a valid issues list.")
        if not isinstance(issue_count, int):
            raise QwenResponseError("Qwen did not return a valid issue_count.")
        return {
            "supported_by_tools": supported_by_tools,
            "has_findings": has_findings,
            "issue_count": issue_count,
            "issues": issues,
        }
