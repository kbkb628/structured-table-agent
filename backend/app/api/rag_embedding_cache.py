from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.rag.embedding_store import refresh_embedding_cache


class EmbeddingCacheRefreshRequest(BaseModel):
    mode: Literal["missing", "stale", "all"]


class EmbeddingCacheRefreshResponse(BaseModel):
    mode: Literal["missing", "stale", "all"]
    model_name: str
    knowledge_item_count: int
    scanned_item_count: int
    refreshed_item_count: int
    missing_refreshed_count: int
    stale_refreshed_count: int
    error_count: int
    elapsed_ms: int


router = APIRouter(prefix="/api/rag/embedding-cache", tags=["rag"])


@router.post("/refresh", response_model=EmbeddingCacheRefreshResponse)
def refresh_embedding_cache_api(request: EmbeddingCacheRefreshRequest) -> EmbeddingCacheRefreshResponse:
    result = refresh_embedding_cache(mode=request.mode)
    return EmbeddingCacheRefreshResponse(**result)
