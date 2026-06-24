REGION_SALES_SUMMARY_TEMPLATE = """
import csv
import json
from collections import defaultdict

totals = defaultdict(float)
with open('/workspace/input/source.csv', 'r', encoding='utf-8-sig', newline='') as fp:
    reader = csv.DictReader(fp)
    for row in reader:
        totals[row['region']] += float(row['sales_amount'] or 0)

top_region = max(totals.items(), key=lambda item: item[1]) if totals else ('none', 0.0)
print(json.dumps({
    'template_name': 'region_sales_summary',
    'top_region': top_region[0],
    'top_sales_amount': round(top_region[1], 2),
    'region_count': len(totals),
}, ensure_ascii=False))
""".strip()


CHANNEL_SALES_SUMMARY_TEMPLATE = """
import csv
import json
from collections import defaultdict

totals = defaultdict(float)
with open('/workspace/input/source.csv', 'r', encoding='utf-8-sig', newline='') as fp:
    reader = csv.DictReader(fp)
    for row in reader:
        totals[row['channel']] += float(row['sales_amount'] or 0)

top_channel = max(totals.items(), key=lambda item: item[1]) if totals else ('none', 0.0)
print(json.dumps({
    'template_name': 'channel_sales_summary',
    'top_channel': top_channel[0],
    'top_sales_amount': round(top_channel[1], 2),
    'channel_count': len(totals),
}, ensure_ascii=False))
""".strip()


def build_sandbox_template_code(template_name: str) -> str:
    templates = {
        "region_sales_summary": REGION_SALES_SUMMARY_TEMPLATE,
        "channel_sales_summary": CHANNEL_SALES_SUMMARY_TEMPLATE,
    }
    try:
        return templates[template_name]
    except KeyError as exc:
        raise ValueError(f"Unknown sandbox template: {template_name}") from exc
