import json
import hashlib
from pathlib import Path
from uuid import uuid4

from app.rag.embedding_store import get_knowledge_embedding
from app.rag.embedding_store import refresh_embedding_cache
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


def test_refresh_embedding_cache_refreshes_missing_items_only(tmp_path: Path, monkeypatch):
    suffix = uuid4().hex
    item_a_id = f"refresh_missing_a_{suffix}"
    item_b_id = f"refresh_missing_b_{suffix}"
    kb_path = tmp_path / "knowledge_base.jsonl"
    kb_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": item_a_id,
                        "title": "Revenue",
                        "content": "sales amount definition",
                        "tags": ["metric"],
                        "related_fields": ["sales_amount"],
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "id": item_b_id,
                        "title": "Region",
                        "content": "region dimension definition",
                        "tags": ["dimension"],
                        "related_fields": ["region"],
                    },
                    ensure_ascii=False,
                ),
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.rag.embedding_store.encode_texts",
        lambda texts: [[float(index + 1), float(index + 2)] for index, _ in enumerate(texts)],
    )

    result = refresh_embedding_cache(mode="missing", knowledge_base_path=kb_path)

    assert result["mode"] == "missing"
    assert result["knowledge_item_count"] == 2
    assert result["refreshed_item_count"] == 2
    assert result["missing_refreshed_count"] == 2
    assert result["stale_refreshed_count"] == 0
    assert result["error_count"] == 0
    assert get_knowledge_embedding(item_a_id) is not None
    assert get_knowledge_embedding(item_b_id) is not None


def test_refresh_embedding_cache_refreshes_stale_items_only(tmp_path: Path, monkeypatch):
    suffix = uuid4().hex
    kb_path = tmp_path / "knowledge_base.jsonl"
    item_a = {
        "id": f"refresh_stale_a_{suffix}",
        "title": "Fresh Item",
        "content": "fresh content",
        "tags": [],
        "related_fields": [],
    }
    item_b = {
        "id": f"refresh_stale_b_{suffix}",
        "title": "Stale Item",
        "content": "stale content",
        "tags": [],
        "related_fields": [],
    }
    kb_path.write_text(
        "\n".join([json.dumps(item_a, ensure_ascii=False), json.dumps(item_b, ensure_ascii=False)]),
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
        embedding=[0.3, 0.4],
    )

    monkeypatch.setattr(
        "app.rag.embedding_store.encode_texts",
        lambda texts: [[9.0, 10.0] for _ in texts],
    )

    result = refresh_embedding_cache(mode="stale", knowledge_base_path=kb_path)

    stale_record = get_knowledge_embedding("refresh_stale_b")
    assert result["mode"] == "stale"
    assert result["refreshed_item_count"] == 1
    assert result["missing_refreshed_count"] == 0
    assert result["stale_refreshed_count"] == 1
    assert stale_record is not None
    assert json.loads(stale_record["embedding_json"]) == [9.0, 10.0]
