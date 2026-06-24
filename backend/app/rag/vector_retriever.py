import hashlib
import json

import numpy as np

from app.core import config
from app.rag.embedding_client import encode_texts
from app.rag.embedding_store import get_knowledge_embedding
from app.rag.embedding_store import upsert_knowledge_embedding


def _build_embedding_text(item: dict) -> str:
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


def _content_hash(item: dict) -> str:
    raw = json.dumps(
        {
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "tags": item.get("tags", []),
            "related_fields": item.get("related_fields", []),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def retrieve_vector_candidates(question: str, knowledge_items: list[dict], top_k: int) -> list[dict]:
    if not knowledge_items:
        return []

    query_vector = np.array(encode_texts([question])[0], dtype=float)
    rows: list[dict] = []

    for item in knowledge_items:
        content_hash = _content_hash(item)
        cached = get_knowledge_embedding(item["id"])
        if cached and cached["content_hash"] == content_hash and cached["model_name"] == config.RAG_BI_ENCODER_MODEL:
            item_vector = np.array(json.loads(cached["embedding_json"]), dtype=float)
        else:
            embedding = encode_texts([_build_embedding_text(item)])[0]
            upsert_knowledge_embedding(
                item_id=item["id"],
                content_hash=content_hash,
                model_name=config.RAG_BI_ENCODER_MODEL,
                embedding=embedding,
            )
            item_vector = np.array(embedding, dtype=float)

        score = float(np.dot(query_vector, item_vector))
        rows.append({"item": item, "embedding_score": round(score, 4)})

    ranked = sorted(rows, key=lambda row: row["embedding_score"], reverse=True)
    return [{**row, "embedding_rank": rank + 1} for rank, row in enumerate(ranked[:top_k])]
