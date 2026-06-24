import json
from datetime import datetime, timezone

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
