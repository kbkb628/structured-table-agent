import json
from pathlib import Path

from app.core.config import KNOWLEDGE_BASE_PATH


def load_knowledge_base(knowledge_base_path: Path | None = None) -> list[dict]:
    path = knowledge_base_path or KNOWLEDGE_BASE_PATH
    if not path.exists():
        return []

    items: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            items.append(json.loads(stripped))
    return items
