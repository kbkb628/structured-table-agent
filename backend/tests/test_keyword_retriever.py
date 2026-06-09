from pathlib import Path

from app.rag.keyword_retriever import retrieve_business_context


def test_retrieve_business_context_matches_region_and_sales_terms(tmp_path: Path):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        "\n".join(
            [
                '{"id":"metric_sales_amount","type":"metric_definition","title":"Sales Amount","content":"Sales amount usually means the order transaction amount.","tags":["sales","metric"],"related_fields":["sales_amount"]}',
                '{"id":"dimension_region","type":"field_definition","title":"Region","content":"Region is used for geographic sales comparison.","tags":["region","dimension"],"related_fields":["region"]}',
                '{"id":"dimension_channel","type":"field_definition","title":"Channel","content":"Channel is used for online and retail performance comparison.","tags":["channel","dimension"],"related_fields":["channel"]}',
            ]
        ),
        encoding="utf-8",
    )

    file_profile = {
        "columns": [
            {"name": "region", "type": "string"},
            {"name": "sales_amount", "type": "number"},
            {"name": "order_id", "type": "string"},
        ]
    }

    result = retrieve_business_context(
        question="analyse sales by region",
        file_profile=file_profile,
        knowledge_base_path=kb_path,
    )

    assert len(result["items"]) >= 2
    assert result["items"][0]["score"] >= result["items"][1]["score"]
    assert {item["id"] for item in result["items"]}.issuperset({"metric_sales_amount", "dimension_region"})


def test_retrieve_business_context_returns_empty_list_when_no_hit(tmp_path: Path):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        '{"id":"dimension_channel","type":"field_definition","title":"Channel","content":"Channel information.","tags":["channel"],"related_fields":["channel"]}' + "\n",
        encoding="utf-8",
    )

    file_profile = {"columns": [{"name": "customer_name", "type": "string"}]}

    result = retrieve_business_context(
        question="analyse refund reasons",
        file_profile=file_profile,
        knowledge_base_path=kb_path,
    )

    assert result == {"items": []}
