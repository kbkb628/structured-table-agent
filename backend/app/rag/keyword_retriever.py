import re
from pathlib import Path

from app.rag.knowledge_loader import load_knowledge_base


def _tokenize(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if token}


def retrieve_business_context(
    question: str,
    file_profile: dict,
    knowledge_base_path: Path | None = None,
    limit: int = 3,
) -> dict:
    knowledge_items = load_knowledge_base(knowledge_base_path)
    if not knowledge_items:
        return {"items": []}

    question_tokens = _tokenize(question)
    file_columns = [column["name"] for column in file_profile.get("columns", [])]
    column_tokens = set()
    for name in file_columns:
        column_tokens.update(_tokenize(name))

    scored_items: list[dict] = []
    for item in knowledge_items:
        title_tokens = _tokenize(item.get("title", ""))
        content_tokens = _tokenize(item.get("content", ""))
        tag_tokens = set()
        for tag in item.get("tags", []):
            tag_tokens.update(_tokenize(tag))
        related_field_tokens = set()
        for field in item.get("related_fields", []):
            related_field_tokens.update(_tokenize(field))

        score = 0.0
        score += len(question_tokens & title_tokens) * 3
        score += len(question_tokens & tag_tokens) * 2
        score += len(question_tokens & content_tokens) * 1
        score += len(column_tokens & related_field_tokens) * 2

        if score <= 0:
            continue

        scored_items.append(
            {
                "id": item["id"],
                "type": item.get("type", ""),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "related_fields": item.get("related_fields", []),
                "score": round(score, 2),
            }
        )

    scored_items.sort(key=lambda item: item["score"], reverse=True)
    return {"items": scored_items[:limit]}
