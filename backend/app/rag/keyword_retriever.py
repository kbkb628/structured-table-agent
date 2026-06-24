from pathlib import Path

from app.core import config
from app.rag.bm25_retriever import retrieve_bm25_candidates
from app.rag.knowledge_loader import load_knowledge_base
from app.rag.reranker import rerank_candidates
from app.rag.vector_retriever import retrieve_vector_candidates


def retrieve_business_context(
    question: str,
    file_profile: dict,
    knowledge_base_path: Path | None = None,
    limit: int = 3,
) -> dict:
    knowledge_items = load_knowledge_base(knowledge_base_path)
    if not knowledge_items:
        return {"items": []}

    bm25_candidates = retrieve_bm25_candidates(
        question=question,
        file_profile=file_profile,
        knowledge_items=knowledge_items,
        top_k=max(limit, config.RAG_BM25_TOP_K),
    )
    vector_candidates = (
        retrieve_vector_candidates(
            question=question,
            knowledge_items=knowledge_items,
            top_k=max(limit, config.RAG_VECTOR_TOP_K),
        )
        if config.RAG_ENABLE_VECTOR_RETRIEVAL
        else []
    )

    merged: dict[str, dict] = {}
    for candidate in bm25_candidates:
        item_id = candidate["item"]["id"]
        merged[item_id] = {
            "item": candidate["item"],
            "bm25_rank": candidate["bm25_rank"],
            "bm25_score": candidate["bm25_score"],
            "embedding_rank": None,
            "embedding_score": None,
            "retrieval_sources": ["bm25"],
        }
    for candidate in vector_candidates:
        item_id = candidate["item"]["id"]
        current = merged.setdefault(
            item_id,
            {
                "item": candidate["item"],
                "bm25_rank": None,
                "bm25_score": 0.0,
                "embedding_rank": None,
                "embedding_score": None,
                "retrieval_sources": [],
            },
        )
        current["embedding_rank"] = candidate["embedding_rank"]
        current["embedding_score"] = candidate["embedding_score"]
        if "embedding" not in current["retrieval_sources"]:
            current["retrieval_sources"].append("embedding")

    merged_candidates = list(merged.values())
    if config.RAG_ENABLE_RERANK:
        ranked_candidates = rerank_candidates(
            question=question,
            candidates=merged_candidates,
            top_k=min(limit, config.RAG_FINAL_TOP_K),
        )
    else:
        ranked_candidates = [
            {**candidate, "rerank_score": None, "final_rank": index + 1}
            for index, candidate in enumerate(merged_candidates[:limit])
        ]

    items = []
    for candidate in ranked_candidates:
        item = candidate["item"]
        score = candidate.get("rerank_score")
        if score is None:
            score = candidate.get("bm25_score") or candidate.get("embedding_score") or 0.0
        items.append(
            {
                "id": item["id"],
                "type": item.get("type", ""),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "related_fields": item.get("related_fields", []),
                "score": round(score, 2),
                "score_breakdown": {
                    "keyword_score": 0.0,
                    "field_score": 0.0,
                    "phrase_score": 0.0,
                    "bm25_score": candidate.get("bm25_score") or 0.0,
                },
                "retrieval_evidence": {
                    "bm25_rank": candidate.get("bm25_rank"),
                    "bm25_score": candidate.get("bm25_score"),
                    "embedding_rank": candidate.get("embedding_rank"),
                    "embedding_score": candidate.get("embedding_score"),
                    "rerank_score": candidate.get("rerank_score"),
                    "final_rank": candidate.get("final_rank"),
                    "retrieval_sources": candidate.get("retrieval_sources") or [],
                },
            }
        )

    return {"items": items}
