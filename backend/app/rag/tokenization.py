import re


def tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-zA-Z0-9_]+", text.lower()) if token]


def tokenize_set(text: str) -> set[str]:
    return set(tokenize(text))


def normalize_text(text: str) -> str:
    return " ".join(tokenize(text))
