"""
Generate documentation screenshot assets from real pipeline output.

Uses Pillow (already installed via Streamlit) — no matplotlib required.
Run: python scripts/generate_screenshot_assets.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.validation_pipeline import run_validation_pipeline
from src.reporting.report_writer import _collect_issue_rows, write_reports

SCREENSHOTS_DIR = PROJECT_ROOT / "docs" / "screenshots"
CONTRACT = "config/data_contracts/customer_orders_contract.yml"
DAY2 = "data/incoming/customer_orders_day2_schema_drift.csv"

WIDTH = 1100
PADDING = 24
LINE_HEIGHT = 18


def _font(size: int = 14):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size)
    except OSError:
        return ImageFont.load_default()


def _save_text_image(filename: str, title: str, lines: list[str], height: int = 700) -> None:
    img = Image.new("RGB", (WIDTH, height), "white")
    draw = ImageDraw.Draw(img)
    title_font = _font(16)
    body_font = _font(13)

    y = PADDING
    draw.text((PADDING, y), title, fill="#111111", font=title_font)
    y += 32

    for line in lines:
        for chunk in wrap(line, width=120) or [""]:
            draw.text((PADDING, y), chunk, fill="#222222", font=body_font)
            y += LINE_HEIGHT
            if y > height - PADDING:
                break

    path = SCREENSHOTS_DIR / filename
    img.save(path)
    print(f"  wrote {path}")


def _bar_chart_image(
    filename: str,
    title: str,
    labels: list[str],
    values: list[int],
    color: str = "#4c78a8",
) -> None:
    height = 420
    img = Image.new("RGB", (WIDTH, height), "white")
    draw = ImageDraw.Draw(img)
    font = _font(13)
    title_font = _font(16)

    draw.text((PADDING, PADDING), title, fill="#111111", font=title_font)
    chart_top = 70
    chart_bottom = height - 60
    chart_left = 120
    chart_right = WIDTH - 40
    max_val = max(values) if values else 1

    for label, value in zip(labels, values):
        pass

    bar_width = (chart_right - chart_left) // max(len(labels), 1) - 20
    for index, (label, value) in enumerate(zip(labels, values)):
        x0 = chart_left + index * (bar_width + 20)
        bar_height = int((value / max_val) * (chart_bottom - chart_top)) if max_val else 0
        y0 = chart_bottom - bar_height
        x1 = x0 + bar_width
        draw.rectangle([x0, y0, x1, chart_bottom], fill=color)
        draw.text((x0, chart_bottom + 8), label, fill="#333333", font=font)
        draw.text((x0, y0 - 18), str(value), fill="#333333", font=font)

    path = SCREENSHOTS_DIR / filename
    img.save(path)
    print(f"  wrote {path}")


def main() -> None:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print("Running Day 2 pipeline for screenshot assets...")
    result = run_validation_pipeline(DAY2, CONTRACT)
    write_reports(result)

    issues = _collect_issue_rows(result)
    severity_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for issue in issues:
        severity_counts[issue["severity"]] = severity_counts.get(issue["severity"], 0) + 1
        category_counts[issue["category"]] = category_counts.get(issue["category"], 0) + 1

    print("Generating images from real validation output...")
    _bar_chart_image(
        "streamlit_overview.png",
        "Issues by Severity (Day 2 Feed)",
        list(severity_counts.keys()),
        list(severity_counts.values()),
        color="#e45756",
    )
    _bar_chart_image(
        "streamlit_schema_drift.png",
        "Issues by Category (Day 2 Feed)",
        list(category_counts.keys()),
        list(category_counts.values()),
    )

    null_lines = [
        f"{col['name']}: {col['null_count']} nulls"
        for col in result["actual_schema"]
        if col.get("null_count", 0) > 0
    ] or ["No null columns detected."]
    _save_text_image(
        "streamlit_data_quality.png",
        "Null Count by Column (Day 2 Feed)",
        null_lines,
        height=360,
    )

    status_col = "order_status" if "order_status" in result["dataframe"].columns else "status"
    if status_col in result["dataframe"].columns:
        counts = result["dataframe"][status_col].fillna("NULL").value_counts()
        status_lines = [f"{idx}: {val}" for idx, val in counts.items()]
        _save_text_image(
            "architecture.png",
            f"{status_col} Distribution (Day 2 Feed)",
            status_lines,
            height=320,
        )

    summary = result["impact_summary"]
    cli_lines = [
        f"Feed: {result['feed_name']}",
        f"Overall Status: {result['overall_status']}",
        f"Risk Level: {result['risk_level']}",
        f"Breaking Changes: {result['breaking_changes_count']}",
        f"Total Issues: {result['total_issues']}",
        "",
        "Executive Summary:",
        summary["executive_summary"],
        "",
        f"Schema issues: {len(result['schema_issues'])}",
        f"Drift issues: {len(result['drift_result'].get('drift_issues', []))}",
        f"Quality issues: {len(result['quality_issues'])}",
    ]
    _save_text_image("cli_output.png", "CLI Validation Output (Day 2)", cli_lines, height=520)

    report_path = PROJECT_ROOT / "data/reports/customer_orders_day2_schema_drift_validation_report.md"
    md_lines = report_path.read_text(encoding="utf-8").splitlines()[:35]
    _save_text_image(
        "markdown_report_preview.png",
        "Markdown Report Preview (Day 2)",
        md_lines,
        height=760,
    )
    print("Done.")


if __name__ == "__main__":
    main()
