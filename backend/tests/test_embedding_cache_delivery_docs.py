from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_embedding_cache_runtime_fields_are_documented():
    repo_root = _repo_root()
    root_readme = (repo_root / "README.md").read_text(encoding="utf-8")
    backend_readme = (repo_root / "backend" / "README.md").read_text(encoding="utf-8")
    api_reference = (repo_root / "docs" / "API_REFERENCE.md").read_text(encoding="utf-8")
    project_status = (repo_root / "docs" / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    interview_guide = (repo_root / "docs" / "INTERVIEW_GUIDE.md").read_text(encoding="utf-8")
    evidence_map = (repo_root / "docs" / "RESUME_EVIDENCE_MAP.md").read_text(encoding="utf-8")

    required_fields = [
        "embedding_cache",
        "knowledge_item_count",
        "cached_item_count",
        "fresh_item_count",
        "stale_item_count",
        "missing_item_count",
        "cache_coverage_ratio",
    ]

    for field in required_fields:
        assert field in root_readme
        assert field in backend_readme
        assert field in api_reference
        assert field in project_status
        assert field in interview_guide

    assert "cache_coverage_ratio" in evidence_map
    assert "stale_item_count" in evidence_map
