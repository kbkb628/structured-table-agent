import json
import hashlib
from pathlib import Path

from app.rag.embedding_store import get_knowledge_embedding
from app.rag.embedding_store import summarize_embedding_cache
from app.rag.embedding_store import upsert_knowledge_embedding


def test_upsert_knowledge_embedding_round_trips_record():
    upsert_knowledge_embedding(
        item_id="analysis_region_sales_embedding_store_round_trip",
        content_hash="hash_001",
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        embedding=[0.1, 0.2, 0.3],
    )

    record = get_knowledge_embedding("analysis_region_sales_embedding_store_round_trip")

    assert record is not None
    assert record["item_id"] == "analysis_region_sales_embedding_store_round_trip"
    assert record["content_hash"] == "hash_001"
    assert record["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert json.loads(record["embedding_json"]) == [0.1, 0.2, 0.3]


def test_summarize_embedding_cache_reports_fresh_and_stale_records(tmp_path: Path):
    kb_path = tmp_path / "knowledge_base.jsonl"
    item_a = {
        "id": "embedding_cache_item_a",
        "title": "Fresh Item",
        "content": "fresh content",
        "tags": [],
        "related_fields": [],
    }
    item_b = {
        "id": "embedding_cache_item_b",
        "title": "Stale Item",
        "content": "stale content",
        "tags": [],
        "related_fields": [],
    }
    kb_path.write_text(
        "\n".join(
            [
                json.dumps(item_a, ensure_ascii=False),
                json.dumps(item_b, ensure_ascii=False),
            ]
        ),
        encoding="utf-8",
    )

    fresh_hash = hashlib.sha256(
        json.dumps(
            {
                "title": item_a["title"],
                "content": item_a["content"],
                "tags": item_a["tags"],
                "related_fields": item_a["related_fields"],
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    upsert_knowledge_embedding(
        item_id=item_a["id"],
        content_hash=fresh_hash,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        embedding=[0.1, 0.2],
    )
    upsert_knowledge_embedding(
        item_id=item_b["id"],
        content_hash="stale_hash",
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        embedding=[0.2, 0.3],
    )

    summary = summarize_embedding_cache(knowledge_base_path=kb_path)

    assert summary["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert summary["knowledge_item_count"] == 2
    assert summary["cached_item_count"] == 2
    assert summary["fresh_item_count"] == 1
    assert summary["stale_item_count"] == 1
    assert summary["missing_item_count"] == 0
    assert summary["cache_coverage_ratio"] == 1.0
