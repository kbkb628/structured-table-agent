from app.sandbox.templates import build_sandbox_template_code


def test_build_region_sales_summary_template_returns_python_code():
    code = build_sandbox_template_code("region_sales_summary")

    assert "import csv" in code
    assert "json.dumps" in code
    assert "source.csv" in code
