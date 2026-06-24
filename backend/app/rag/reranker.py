from app.core import config

_reranker = None


def get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers.cross_encoder import CrossEncoder

        _reranker = CrossEncoder(config.RAG_RERANK_MODEL)
    return _reranker


def rerank_candidates(question: str, candidates: list[dict], top_k: int) -> list[dict]:
    if not candidates:
        return []

    pairs = [
        (
            question,
            " ".join(
                segment
                for segment in [
                    str(candidate["item"].get("title", "")),
                    str(candidate["item"].get("content", "")),
                ]
                if segment
            ),
        )
        for candidate in candidates
    ]
    scores = get_reranker().predict(pairs)
    ranked = sorted(
        [{**candidate, "rerank_score": round(float(score), 4)} for candidate, score in zip(candidates, scores, strict=True)],
        key=lambda row: row["rerank_score"],
        reverse=True,
    )
    return [{**row, "final_rank": rank + 1} for rank, row in enumerate(ranked[:top_k])]
