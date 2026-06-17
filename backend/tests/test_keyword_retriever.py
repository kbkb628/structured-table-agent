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


def test_retrieve_business_context_prefers_phrase_and_field_aligned_item(tmp_path: Path):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        "\n".join(
            [
                '{"id":"analysis_region_sales","type":"analysis_template","title":"Sales By Region","content":"Sales by region analysis compares regional sales totals and geographic performance.","tags":["sales by region","region","sales"],"related_fields":["region","sales_amount"]}',
                '{"id":"analysis_generic_sales","type":"analysis_template","title":"Sales Analysis","content":"General sales analysis can compare many dimensions and metrics.","tags":["sales","analysis"],"related_fields":[]}',
                '{"id":"dimension_region_only","type":"field_definition","title":"Region","content":"Region dimension.","tags":["region"],"related_fields":["region"]}',
            ]
        ),
        encoding="utf-8",
    )

    file_profile = {
        "columns": [
            {"name": "region", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    result = retrieve_business_context(
        question="analyse sales by region",
        file_profile=file_profile,
        knowledge_base_path=kb_path,
    )

    assert result["items"][0]["id"] == "analysis_region_sales"
    assert result["items"][0]["score"] > result["items"][1]["score"]


def test_retrieve_business_context_prefers_order_count_channel_template(tmp_path: Path):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        "\n".join(
            [
                '{"id":"analysis_channel_orders","type":"analysis_template","title":"Channel Order Count Analysis","content":"Analyse order count and sales performance by channel.","tags":["order count","channel","sales"],"related_fields":["channel","order_id","sales_amount"]}',
                '{"id":"analysis_channel_sales","type":"analysis_template","title":"Channel Sales Analysis","content":"Analyse sales amount by channel.","tags":["channel","sales"],"related_fields":["channel","sales_amount"]}',
            ]
        ),
        encoding="utf-8",
    )

    file_profile = {
        "columns": [
            {"name": "channel", "type": "string"},
            {"name": "order_id", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    result = retrieve_business_context(
        question="analyse channel order count and sales performance",
        file_profile=file_profile,
        knowledge_base_path=kb_path,
    )

    assert result["items"][0]["id"] == "analysis_channel_orders"


def test_retrieve_business_context_includes_score_breakdown(tmp_path: Path):
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        '{"id":"dimension_region","type":"field_definition","title":"Region","content":"Region is used for geographic sales comparison.","tags":["region","dimension"],"related_fields":["region"]}' + "\n",
        encoding="utf-8",
    )

    file_profile = {"columns": [{"name": "region", "type": "string"}]}

    result = retrieve_business_context(
        question="analyse sales by region",
        file_profile=file_profile,
        knowledge_base_path=kb_path,
    )

    assert "score_breakdown" in result["items"][0]
    assert "keyword_score" in result["items"][0]["score_breakdown"]
    assert "bm25_score" in result["items"][0]["score_breakdown"]
    assert "phrase_score" in result["items"][0]["score_breakdown"]


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
