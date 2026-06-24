from app.rag.tokenization import tokenize


def _build_document_text(item: dict) -> str:
    return " ".join(
        segment
        for segment in [
            str(item.get("title", "")),
            str(item.get("content", "")),
            " ".join(item.get("tags", [])),
            " ".join(item.get("related_fields", [])),
        ]
        if segment
    )


def build_bm25_corpus(knowledge_items: list[dict]):
    from rank_bm25 import BM25Plus

    tokenized_corpus: list[list[str]] = []
    for item in knowledge_items:
        tokenized_corpus.append(tokenize(_build_document_text(item)))
    return knowledge_items, tokenized_corpus, BM25Plus(tokenized_corpus)


def retrieve_bm25_candidates(
    question: str,
    file_profile: dict,
    knowledge_items: list[dict],
    top_k: int,
) -> list[dict]:
    items, _, bm25 = build_bm25_corpus(knowledge_items)
    query_tokens = tokenize(question) + [
        token
        for column in file_profile.get("columns", [])
        for token in tokenize(column["name"])
    ]
    scores = bm25.get_scores(query_tokens)
    ranked_rows = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
    ranked = [
        {
            "item": items[index],
            "bm25_rank": rank + 1,
            "bm25_score": round(float(score), 4),
        }
        for rank, (index, score) in enumerate(ranked_rows)
        if score > 0
    ]
    return ranked[:top_k]
