from app.rag.reranker import rerank_candidates


def test_rerank_candidates_reorders_merged_results(monkeypatch):
    candidates = [
        {"item": {"id": "analysis_region_sales", "title": "Sales By Region", "content": "Compare region sales."}},
        {"item": {"id": "analysis_channel_orders", "title": "Channel Orders", "content": "Compare channel orders."}},
    ]

    class StubReranker:
        def predict(self, pairs):
            return [0.97, 0.11]

    monkeypatch.setattr("app.rag.reranker.get_reranker", lambda: StubReranker())

    ranked = rerank_candidates(
        question="analyse sales by region",
        candidates=candidates,
        top_k=2,
    )

    assert ranked[0]["item"]["id"] == "analysis_region_sales"
    assert ranked[0]["rerank_score"] == 0.97
    assert ranked[0]["final_rank"] == 1
