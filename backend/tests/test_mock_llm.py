from app.llm.mock_client import MockLLMClient


def test_mock_llm_generates_region_goal_from_question_and_context():
    client = MockLLMClient()
    file_profile = {"columns": [{"name": "region", "type": "string"}, {"name": "sales_amount", "type": "number"}]}
    business_context = [
        {"id": "dimension_region", "title": "Region", "content": "Region is used for geographic sales comparison.", "score": 0.9},
        {"id": "metric_sales_amount", "title": "Sales Amount", "content": "Sales amount usually means the order transaction amount.", "score": 0.8},
    ]

    goal = client.generate_analysis_goal(
        question="analyse sales by region",
        file_profile=file_profile,
        business_context=business_context,
    )

    assert "region" in goal.lower()
    assert "sales" in goal.lower()


def test_mock_llm_generates_channel_plan_with_two_steps():
    client = MockLLMClient()
    analysis_goal = "compare channel order and sales performance"
    file_profile = {"columns": [{"name": "channel", "type": "string"}, {"name": "order_id", "type": "string"}]}
    business_context = [{"id": "dimension_channel", "title": "Channel", "content": "Channel comparison.", "score": 0.7}]

    plan = client.generate_analysis_plan(
        analysis_goal=analysis_goal,
        file_profile=file_profile,
        business_context=business_context,
    )

    assert len(plan) >= 4
    assert any("channel" in step.lower() for step in plan)
    assert any("order" in step.lower() for step in plan)
    assert any("sales" in step.lower() for step in plan)
