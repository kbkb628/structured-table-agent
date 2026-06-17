import re
from math import log
from pathlib import Path

from app.rag.knowledge_loader import load_knowledge_base


def _tokenize(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if token}


def _tokenize_list(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if token]


def _normalize_text(text: str) -> str:
    return " ".join(_tokenize_list(text))


def _phrase_variants(question: str) -> set[str]:
    normalized = _normalize_text(question)
    variants = {normalized} if normalized else set()
    tokens = normalized.split()
    if len(tokens) >= 2:
        variants.update(" ".join(tokens[index:index + 2]) for index in range(len(tokens) - 1))
    if len(tokens) >= 3:
        variants.update(" ".join(tokens[index:index + 3]) for index in range(len(tokens) - 2))
    return variants


def _collect_document_tokens(item: dict) -> list[str]:
    segments = [item.get("title", ""), item.get("content", "")]
    segments.extend(item.get("tags", []))
    segments.extend(item.get("related_fields", []))
    tokens: list[str] = []
    for segment in segments:
        tokens.extend(_tokenize_list(str(segment)))
    return tokens


def _build_document_frequencies(knowledge_items: list[dict]) -> tuple[dict[str, int], dict[str, list[str]], float]:
    document_tokens: dict[str, list[str]] = {}
    document_frequencies: dict[str, int] = {}
    total_length = 0

    for item in knowledge_items:
        tokens = _collect_document_tokens(item)
        document_tokens[item["id"]] = tokens
        total_length += len(tokens)
        for token in set(tokens):
            document_frequencies[token] = document_frequencies.get(token, 0) + 1

    average_length = total_length / len(knowledge_items) if knowledge_items else 0.0
    return document_frequencies, document_tokens, average_length


def _bm25_score(
    query_tokens: set[str],
    tokens: list[str],
    document_frequencies: dict[str, int],
    document_count: int,
    average_length: float,
) -> float:
    if not query_tokens or not tokens or document_count == 0 or average_length == 0:
        return 0.0

    term_counts: dict[str, int] = {}
    for token in tokens:
        term_counts[token] = term_counts.get(token, 0) + 1

    score = 0.0
    k1 = 1.5
    b = 0.75
    document_length = len(tokens)
    for token in query_tokens:
        frequency = term_counts.get(token, 0)
        if frequency == 0:
            continue
        document_frequency = document_frequencies.get(token, 0)
        idf = log(1 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5))
        numerator = frequency * (k1 + 1)
        denominator = frequency + k1 * (1 - b + b * document_length / average_length)
        score += idf * (numerator / denominator)
    return score


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
    question_phrases = _phrase_variants(question)
    file_columns = [column["name"] for column in file_profile.get("columns", [])]
    column_tokens = set()
    for name in file_columns:
        column_tokens.update(_tokenize(name))

    document_frequencies, document_tokens, average_length = _build_document_frequencies(knowledge_items)
    document_count = len(knowledge_items)
    scored_items: list[dict] = []

    for item in knowledge_items:
        title_tokens = _tokenize(item.get("title", ""))
        content_tokens = _tokenize(item.get("content", ""))
        normalized_title = _normalize_text(item.get("title", ""))
        normalized_content = _normalize_text(item.get("content", ""))
        normalized_tags = [_normalize_text(tag) for tag in item.get("tags", [])]

        tag_tokens = set()
        for tag in item.get("tags", []):
            tag_tokens.update(_tokenize(tag))

        related_field_tokens = set()
        for field in item.get("related_fields", []):
            related_field_tokens.update(_tokenize(field))

        keyword_score = 0.0
        keyword_score += len(question_tokens & title_tokens) * 3
        keyword_score += len(question_tokens & tag_tokens) * 2
        keyword_score += len(question_tokens & content_tokens) * 1

        field_score = len(column_tokens & related_field_tokens) * 2
        phrase_score = 0.0
        for phrase in question_phrases:
            if phrase and (
                phrase in normalized_title
                or phrase in normalized_content
                or any(phrase == tag or phrase in tag for tag in normalized_tags)
            ):
                phrase_score += 4.0

        bm25_score = round(
            _bm25_score(
                question_tokens | column_tokens,
                document_tokens.get(item["id"], []),
                document_frequencies,
                document_count,
                average_length,
            ),
            4,
        )
        score = keyword_score + field_score + phrase_score + bm25_score

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
                "score_breakdown": {
                    "keyword_score": round(keyword_score, 2),
                    "field_score": round(field_score, 2),
                    "phrase_score": round(phrase_score, 2),
                    "bm25_score": round(bm25_score, 4),
                },
            }
        )

    scored_items.sort(key=lambda item: item["score"], reverse=True)
    return {"items": scored_items[:limit]}
