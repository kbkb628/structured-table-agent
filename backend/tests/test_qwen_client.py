import json

import pytest
from urllib.error import HTTPError

from app.schemas.report_schema import FinalReport


class StubResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type
        del exc
        del tb
        return False


def _chat_payload(content: str) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": content,
                }
            }
        ]
    }


def test_qwen_client_parses_goal_response(monkeypatch):
    from app.llm.qwen_client import QwenClient

    monkeypatch.setattr(
        "app.llm.qwen_client.urlopen",
        lambda request, timeout: StubResponse(
            200,
            _chat_payload(json.dumps({"analysis_goal": "Compare regional sales performance"})),
        ),
    )

    client = QwenClient(api_key="test-key", base_url="https://example.com/v1", model="qwen-plus")
    goal = client.generate_analysis_goal(
        question="analyse sales by region",
        file_profile={"columns": [{"name": "region"}, {"name": "sales_amount"}]},
        business_context=[{"title": "Region"}],
    )

    assert goal == "Compare regional sales performance"


def test_qwen_client_parses_plan_response(monkeypatch):
    from app.llm.qwen_client import QwenClient

    monkeypatch.setattr(
        "app.llm.qwen_client.urlopen",
        lambda request, timeout: StubResponse(
            200,
            _chat_payload(json.dumps({"analysis_plan": ["match region", "aggregate sales"]})),
        ),
    )

    client = QwenClient(api_key="test-key", base_url="https://example.com/v1", model="qwen-plus")
    plan = client.generate_analysis_plan(
        analysis_goal="Compare regional sales performance",
        file_profile={"columns": [{"name": "region"}, {"name": "sales_amount"}]},
        business_context=[{"title": "Region"}],
    )

    assert plan == ["match region", "aggregate sales"]


def test_qwen_client_generates_schema_valid_report(monkeypatch):
    from app.llm.qwen_client import QwenClient

    monkeypatch.setattr(
        "app.llm.qwen_client.urlopen",
        lambda request, timeout: StubResponse(
            200,
            _chat_payload(
                json.dumps(
                    {
                        "title": "Regional Sales Report",
                        "analysis_goal": "Compare regional sales performance",
                        "key_findings": [
                            {
                                "finding": "East performs best",
                                "evidence": "East has the highest sales_amount_sum",
                                "source_tool": "groupby_aggregate",
                            }
                        ],
                        "chart_explanations": ["Bar chart compares regional sales totals."],
                        "business_suggestions": ["Focus on East best practices."],
                        "data_limitations": ["Based only on uploaded sales data."],
                        "next_steps": ["Segment region performance further."],
                    }
                )
            ),
        ),
    )

    client = QwenClient(api_key="test-key", base_url="https://example.com/v1", model="qwen-plus")
    report = client.generate_report(
        analysis_goal="Compare regional sales performance",
        intermediate_findings=[{"summary": "East performs best"}],
        chart_specs=[{"chart_type": "bar"}],
        business_context=[{"title": "Region"}],
    )

    validated = FinalReport.model_validate(report)
    assert validated.title == "Regional Sales Report"


def test_qwen_client_raises_on_invalid_json(monkeypatch):
    from app.llm.qwen_client import QwenClient, QwenResponseError

    monkeypatch.setattr(
        "app.llm.qwen_client.urlopen",
        lambda request, timeout: StubResponse(
            200,
            _chat_payload("not-json"),
        ),
    )

    client = QwenClient(api_key="test-key", base_url="https://example.com/v1", model="qwen-plus")

    with pytest.raises(QwenResponseError):
        client.generate_analysis_goal(
            question="analyse sales by region",
            file_profile={"columns": [{"name": "region"}, {"name": "sales_amount"}]},
            business_context=[{"title": "Region"}],
        )


def test_qwen_client_reports_api_key_source_on_http_error(monkeypatch):
    from app.llm.qwen_client import QwenClient, QwenResponseError

    class StubErrorBody:
        def read(self):
            return b'{"error":{"code":"invalid_api_key"}}'

        def close(self):
            return None

    def _raise_http_error(request, timeout):
        del request
        del timeout
        raise HTTPError(
            url="https://example.com/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=StubErrorBody(),
        )

    monkeypatch.setattr("app.llm.qwen_client.urlopen", _raise_http_error)

    client = QwenClient(
        api_key="test-key",
        api_key_source="OPENAI_API_KEY_0011AI",
        base_url="https://example.com/v1",
        model="qwen-plus",
    )

    with pytest.raises(QwenResponseError) as exc_info:
        client.generate_analysis_goal(
            question="analyse sales by region",
            file_profile={"columns": [{"name": "region"}, {"name": "sales_amount"}]},
            business_context=[{"title": "Region"}],
        )

    assert "api_key_source=OPENAI_API_KEY_0011AI" in str(exc_info.value)
