import json
import time
from hashlib import sha256
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal

from app.core import config
from app.rag.embedding_client import encode_texts
from app.rag.knowledge_loader import load_knowledge_base
from app.storage.database import get_connection
from app.storage.database import init_db

RefreshMode = Literal["missing", "stale", "all"]


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


def _load_cached_embedding_rows(item_ids: list[str]) -> dict[str, tuple[str, str]]:
    if not item_ids:
        return {}

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
    return {row[0]: (row[1], row[2]) for row in rows}


def _needs_refresh(item: dict, cached: tuple[str, str] | None, mode: RefreshMode) -> tuple[bool, str | None]:
    expected_hash = _knowledge_item_content_hash(item)

    if mode == "all":
        if cached is None:
            return True, "missing"
        cached_hash, cached_model_name = cached
        if cached_hash != expected_hash or cached_model_name != config.RAG_BI_ENCODER_MODEL:
            return True, "stale"
        return True, "fresh"

    if cached is None:
        return (mode == "missing"), "missing"

    cached_hash, cached_model_name = cached
    is_stale = cached_hash != expected_hash or cached_model_name != config.RAG_BI_ENCODER_MODEL
    if mode == "stale" and is_stale:
        return True, "stale"
    return False, "fresh" if not is_stale else "stale"


def refresh_embedding_cache(mode: RefreshMode, knowledge_base_path: Path | None = None) -> dict:
    started = time.perf_counter()
    knowledge_items = load_knowledge_base(knowledge_base_path)
    item_ids = [item["id"] for item in knowledge_items if item.get("id")]
    cached_rows = _load_cached_embedding_rows(item_ids)

    refreshed_item_count = 0
    missing_refreshed_count = 0
    stale_refreshed_count = 0

    for item in knowledge_items:
        item_id = item.get("id")
        if not item_id:
            continue

        should_refresh, reason = _needs_refresh(item, cached_rows.get(item_id), mode)
        if not should_refresh:
            continue

        embedding = encode_texts([_build_embedding_text(item)])[0]
        upsert_knowledge_embedding(
            item_id=item_id,
            content_hash=_knowledge_item_content_hash(item),
            model_name=config.RAG_BI_ENCODER_MODEL,
            embedding=embedding,
        )
        refreshed_item_count += 1
        if reason == "missing":
            missing_refreshed_count += 1
        elif reason == "stale":
            stale_refreshed_count += 1

    return {
        "mode": mode,
        "model_name": config.RAG_BI_ENCODER_MODEL,
        "knowledge_item_count": len(knowledge_items),
        "scanned_item_count": len(knowledge_items),
        "refreshed_item_count": refreshed_item_count,
        "missing_refreshed_count": missing_refreshed_count,
        "stale_refreshed_count": stale_refreshed_count,
        "error_count": 0,
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }


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
    cached_rows = _load_cached_embedding_rows(item_ids)

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
