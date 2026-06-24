from app.rag.bm25_retriever import retrieve_bm25_candidates


def test_retrieve_bm25_candidates_prefers_region_sales_template():
    knowledge_items = [
        {
            "id": "analysis_region_sales",
            "title": "Sales By Region",
            "content": "Compare regional sales totals.",
            "tags": ["sales", "region"],
            "related_fields": ["region", "sales_amount"],
        },
        {
            "id": "analysis_channel_orders",
            "title": "Channel Order Count Analysis",
            "content": "Compare channel order counts.",
            "tags": ["channel", "orders"],
            "related_fields": ["channel", "order_id"],
        },
    ]
    file_profile = {
        "columns": [
            {"name": "region", "type": "string"},
            {"name": "sales_amount", "type": "number"},
        ]
    }

    candidates = retrieve_bm25_candidates(
        question="analyse sales by region",
        file_profile=file_profile,
        knowledge_items=knowledge_items,
        top_k=3,
    )

    assert candidates[0]["item"]["id"] == "analysis_region_sales"
    assert candidates[0]["bm25_rank"] == 1
    assert candidates[0]["bm25_score"] > 0
