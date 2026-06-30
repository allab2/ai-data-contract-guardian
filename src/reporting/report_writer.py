"""
report_writer.py
----------------
Writes validation pipeline results to JSON, Markdown, and CSV reports.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _report_stem(feed_name: str) -> str:
    return Path(feed_name).stem


def _collect_issue_rows(pipeline_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten schema, drift, and quality issues into CSV-friendly rows."""
    rows: list[dict[str, Any]] = []

    for issue in pipeline_result.get("schema_issues", []):
        rows.append(
            {
                "category": "schema_validation",
                "issue_type": issue.get("issue_type", ""),
                "severity": issue.get("severity", ""),
                "column": issue.get("column", ""),
                "message": issue.get("message", ""),
                "is_breaking_change": issue.get("is_breaking_change", False),
            }
        )

    for issue in pipeline_result.get("drift_result", {}).get("drift_issues", []):
        rows.append(
            {
                "category": "schema_drift",
                "issue_type": issue.get("issue_type", ""),
                "severity": issue.get("severity", ""),
                "column": issue.get("column", ""),
                "message": issue.get("message", ""),
                "is_breaking_change": issue.get("is_breaking_change", False),
            }
        )

    for issue in pipeline_result.get("quality_issues", []):
        rows.append(
            {
                "category": "data_quality",
                "issue_type": issue.get("issue_type", ""),
                "severity": issue.get("severity", ""),
                "column": issue.get("column", ""),
                "message": issue.get("message", ""),
                "is_breaking_change": False,
            }
        )

    return rows


def build_json_report(pipeline_result: dict[str, Any]) -> dict[str, Any]:
    """Build the JSON-serializable report payload."""
    impact_summary = pipeline_result["impact_summary"]
    return {
        "feed_name": pipeline_result["feed_name"],
        "run_timestamp": pipeline_result["run_timestamp"],
        "overall_status": pipeline_result["overall_status"],
        "risk_level": pipeline_result["risk_level"],
        "schema_issues": pipeline_result["schema_issues"],
        "drift_result": pipeline_result["drift_result"],
        "quality_issues": pipeline_result["quality_issues"],
        "impact_summary": impact_summary,
        "recommended_actions": impact_summary.get("recommended_actions", []),
    }


def build_markdown_report(pipeline_result: dict[str, Any]) -> str:
    """Build a GitHub-readable Markdown validation report."""
    impact = pipeline_result["impact_summary"]
    drift = pipeline_result["drift_result"]
    lines = [
        f"# Validation Report: {pipeline_result['feed_name']}",
        "",
        f"**Run timestamp:** {pipeline_result['run_timestamp']}",
        "",
        "## Executive Summary",
        "",
        impact["executive_summary"],
        "",
        "## Overall Status",
        "",
        f"- **Status:** {pipeline_result['overall_status']}",
        f"- **Risk level:** {pipeline_result['risk_level']}",
        f"- **Breaking changes:** {pipeline_result['breaking_changes_count']}",
        f"- **Total issues:** {pipeline_result['total_issues']}",
        "",
        "## Schema Validation",
        "",
    ]

    if pipeline_result["schema_issues"]:
        for issue in pipeline_result["schema_issues"]:
            lines.append(
                f"- **[{issue.get('severity', '').upper()}]** "
                f"`{issue.get('issue_type')}` ({issue.get('column')}): "
                f"{issue.get('message')}"
            )
    else:
        lines.append("- No schema validation issues detected.")

    lines.extend(["", "## Schema Drift", ""])
    if drift.get("has_drift"):
        lines.append(
            f"Drift detected: {drift.get('breaking_changes_count', 0)} breaking, "
            f"{drift.get('non_breaking_changes_count', 0)} non-breaking."
        )
        lines.append("")
        for issue in drift.get("drift_issues", []):
            breaking = "breaking" if issue.get("is_breaking_change") else "non-breaking"
            lines.append(
                f"- **[{issue.get('severity', '').upper()}]** "
                f"`{issue.get('issue_type')}` ({issue.get('column')}, {breaking}): "
                f"{issue.get('message')}"
            )
    else:
        lines.append("- No schema drift detected.")

    lines.extend(["", "## Data Quality Issues", ""])
    if pipeline_result["quality_issues"]:
        for issue in pipeline_result["quality_issues"]:
            lines.append(
                f"- **[{issue.get('severity', '').upper()}]** "
                f"`{issue.get('issue_type')}` ({issue.get('column')}): "
                f"{issue.get('message')}"
            )
    else:
        lines.append("- No data quality issues detected.")

    lines.extend(["", "## Recommended Actions", ""])
    for index, action in enumerate(impact.get("recommended_actions", []), start=1):
        lines.append(f"{index}. {action}")

    lines.extend(["", "## Downstream Impact", "", impact.get("downstream_impact", "")])
    return "\n".join(lines) + "\n"


def write_reports(
    pipeline_result: dict[str, Any],
    output_dir: str = "data/reports",
) -> dict[str, str]:
    """Write JSON, Markdown, and CSV reports for a pipeline run.

    Returns:
        Dictionary with paths to generated report files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    stem = _report_stem(pipeline_result["feed_name"])
    json_path = output_path / f"{stem}_validation_report.json"
    md_path = output_path / f"{stem}_validation_report.md"
    csv_path = output_path / f"{stem}_issues.csv"

    json_payload = build_json_report(pipeline_result)
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(json_payload, json_file, indent=2, default=str)

    markdown_content = build_markdown_report(pipeline_result)
    md_path.write_text(markdown_content, encoding="utf-8")

    issue_rows = _collect_issue_rows(pipeline_result)
    fieldnames = [
        "category",
        "issue_type",
        "severity",
        "column",
        "message",
        "is_breaking_change",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(issue_rows)

    return {
        "json": str(json_path),
        "markdown": str(md_path),
        "csv": str(csv_path),
    }
