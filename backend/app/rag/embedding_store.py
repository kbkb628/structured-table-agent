import json
from hashlib import sha256
from pathlib import Path
from datetime import datetime, timezone

from app.core import config
from app.rag.knowledge_loader import load_knowledge_base
from app.storage.database import get_connection
from app.storage.database import init_db


def _ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_knowledge_embedding(item_id: str) -> dict | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT item_id, content_hash, embedding_json, model_name, vector_dim, updated_at
            FROM knowledge_embeddings
            WHERE item_id = ?
            """,
            (item_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "item_id": row[0],
        "content_hash": row[1],
        "embedding_json": row[2],
        "model_name": row[3],
        "vector_dim": row[4],
        "updated_at": row[5],
    }


def upsert_knowledge_embedding(
    item_id: str,
    content_hash: str,
    model_name: str,
    embedding: list[float],
) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO knowledge_embeddings (
                item_id, content_hash, embedding_json, model_name, vector_dim, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                content_hash = excluded.content_hash,
                embedding_json = excluded.embedding_json,
                model_name = excluded.model_name,
                vector_dim = excluded.vector_dim,
                updated_at = excluded.updated_at
            """,
            (
                item_id,
                content_hash,
                json.dumps(embedding, ensure_ascii=False),
                model_name,
                len(embedding),
                _ts(),
            ),
        )


def _knowledge_item_content_hash(item: dict) -> str:
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
    return sha256(raw.encode("utf-8")).hexdigest()


def summarize_embedding_cache(knowledge_base_path: Path | None = None) -> dict:
    knowledge_items = load_knowledge_base(knowledge_base_path)
    knowledge_item_count = len(knowledge_items)
    if knowledge_item_count == 0:
        return {
            "model_name": config.RAG_BI_ENCODER_MODEL,
            "knowledge_item_count": 0,
            "cached_item_count": 0,
            "fresh_item_count": 0,
            "stale_item_count": 0,
            "missing_item_count": 0,
            "cache_coverage_ratio": 0.0,
        }

    item_ids = [item["id"] for item in knowledge_items if item.get("id")]
    cached_rows: dict[str, tuple[str, str]] = {}
    if item_ids:
        placeholders = ", ".join("?" for _ in item_ids)
        init_db()
        with get_connection() as conn:
            rows = conn.execute(
                f"""
                SELECT item_id, content_hash, model_name
                FROM knowledge_embeddings
                WHERE item_id IN ({placeholders})
                """,
                tuple(item_ids),
            ).fetchall()
        cached_rows = {row[0]: (row[1], row[2]) for row in rows}

    fresh_item_count = 0
    stale_item_count = 0
    cached_item_count = 0
    for item in knowledge_items:
        item_id = item.get("id")
        if not item_id:
            continue
        cached = cached_rows.get(item_id)
        if cached is None:
            continue
        cached_item_count += 1
        expected_hash = _knowledge_item_content_hash(item)
        cached_hash, cached_model_name = cached
        if cached_hash == expected_hash and cached_model_name == config.RAG_BI_ENCODER_MODEL:
            fresh_item_count += 1
        else:
            stale_item_count += 1

    missing_item_count = max(knowledge_item_count - cached_item_count, 0)
    return {
        "model_name": config.RAG_BI_ENCODER_MODEL,
        "knowledge_item_count": knowledge_item_count,
        "cached_item_count": cached_item_count,
        "fresh_item_count": fresh_item_count,
        "stale_item_count": stale_item_count,
        "missing_item_count": missing_item_count,
        "cache_coverage_ratio": round(cached_item_count / knowledge_item_count, 4),
    }
