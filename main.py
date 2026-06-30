"""
main.py
-------
CLI entry point for the AI Data Contract & Schema Drift Guardian.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline.validation_pipeline import DEFAULT_CONTRACT_PATH, run_validation_pipeline
from src.reporting.report_writer import write_reports


def _print_section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def _print_issues(issues: list[dict], empty_message: str) -> None:
    if not issues:
        print(f"  {empty_message}")
        return

    for index, issue in enumerate(issues, start=1):
        column = issue.get("column") or "dataset"
        severity = issue.get("severity", "n/a")
        issue_type = issue.get("issue_type", "issue")
        message = issue.get("message", "")
        print(f"  {index}. [{severity.upper()}] {issue_type} ({column})")
        print(f"     {message}")


def print_console_summary(result: dict) -> None:
    """Print a readable console report from a pipeline result."""
    summary = result["impact_summary"]
    drift_result = result["drift_result"]

    print("\n" + "=" * 72)
    print("AI DATA CONTRACT & SCHEMA DRIFT GUARDIAN - VALIDATION REPORT")
    print("=" * 72)
    print(f"Feed:              {result['feed_name']}")
    print(f"Overall Status:    {result['overall_status']}")
    print(f"Risk Level:        {result['risk_level']}")
    print(f"Total Issues:      {result['total_issues']}")
    print(f"Breaking Changes:  {result['breaking_changes_count']}")

    _print_section("Executive Summary")
    print(f"  {summary['executive_summary']}")

    _print_section("Schema Validation")
    _print_issues(result["schema_issues"], "No schema issues detected.")

    _print_section("Schema Drift")
    if drift_result.get("has_drift"):
        print(
            f"  Drift detected: {drift_result['breaking_changes_count']} breaking, "
            f"{drift_result['non_breaking_changes_count']} non-breaking."
        )
        _print_issues(drift_result.get("drift_issues", []), "")
    else:
        print("  No schema drift detected.")

    _print_section("Data Quality")
    _print_issues(result["quality_issues"], "No data quality issues detected.")

    _print_section("Downstream Impact")
    print(f"  {summary['downstream_impact']}")

    _print_section("Recommended Actions")
    for index, action in enumerate(summary["recommended_actions"], start=1):
        print(f"  {index}. {action}")

    print("\n" + "=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate incoming data feeds against YAML data contracts."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the incoming CSV file (e.g. data/incoming/customer_orders_day1.csv)",
    )
    parser.add_argument(
        "--contract",
        default=DEFAULT_CONTRACT_PATH,
        help=f"Path to the YAML data contract (default: {DEFAULT_CONTRACT_PATH})",
    )
    parser.add_argument(
        "--reports-dir",
        default="data/reports",
        help="Directory for generated reports (default: data/reports)",
    )
    args = parser.parse_args()

    print(f"Running validation pipeline for: {args.file}")
    result = run_validation_pipeline(args.file, args.contract)
    print(
        f"  -> Loaded {result['row_count']} rows, {result['column_count']} columns "
        f"against contract {Path(args.contract).name}"
    )

    report_paths = write_reports(result, output_dir=args.reports_dir)
    print_console_summary(result)

    print("\nReports saved:")
    print(f"  JSON:     {report_paths['json']}")
    print(f"  Markdown: {report_paths['markdown']}")
    print(f"  CSV:      {report_paths['csv']}")


if __name__ == "__main__":
    main()
