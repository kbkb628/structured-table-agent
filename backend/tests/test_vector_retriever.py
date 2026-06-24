from app.rag.vector_retriever import retrieve_vector_candidates


def test_retrieve_vector_candidates_uses_embedding_similarity(monkeypatch):
    knowledge_items = [
        {"id": "analysis_region_sales", "title": "Sales By Region", "content": "Compare region sales.", "tags": [], "related_fields": []},
        {"id": "analysis_channel_orders", "title": "Channel Orders", "content": "Compare channel orders.", "tags": [], "related_fields": []},
    ]

    def fake_encode_texts(texts: list[str]) -> list[list[float]]:
        mapping = {
            "analyse sales by region": [1.0, 0.0],
            "Sales By Region Compare region sales.": [1.0, 0.0],
            "Channel Orders Compare channel orders.": [0.0, 1.0],
        }
        return [mapping[text] for text in texts]

    monkeypatch.setattr("app.rag.vector_retriever.encode_texts", fake_encode_texts)

    candidates = retrieve_vector_candidates(
        question="analyse sales by region",
        knowledge_items=knowledge_items,
        top_k=2,
    )

    assert candidates[0]["item"]["id"] == "analysis_region_sales"
    assert candidates[0]["embedding_rank"] == 1
    assert candidates[0]["embedding_score"] > candidates[1]["embedding_score"]
