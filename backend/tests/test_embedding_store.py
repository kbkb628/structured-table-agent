import json

from app.rag.embedding_store import get_knowledge_embedding
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
