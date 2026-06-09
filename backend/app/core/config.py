from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
SAMPLE_DIR = DATA_DIR / "samples"
DB_PATH = BASE_DIR / "app.db"
KNOWLEDGE_BASE_PATH = BASE_DIR / "app" / "rag" / "knowledge_base.jsonl"
