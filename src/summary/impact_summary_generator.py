"""
impact_summary_generator.py
---------------------------
Generates plain-English impact summaries from validation findings and
drift events using rule-based templates (no external AI API).
"""

from __future__ import annotations

from typing import Any

_SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def _max_severity(severities: list[str]) -> str:
    if not severities:
        return "LOW"
    ranked = max(severities, key=lambda item: _SEVERITY_ORDER.get(item, 0))
    return ranked.upper()


def _has_critical_schema_issue(schema_issues: list[dict[str, Any]]) -> bool:
    return any(issue.get("severity") == "critical" for issue in schema_issues)


def _has_missing_required_column(schema_issues: list[dict[str, Any]]) -> bool:
    return any(
        issue.get("issue_type") == "missing_column" and issue.get("is_breaking_change")
        for issue in schema_issues
    )


def _collect_breaking_changes(
    schema_issues: list[dict[str, Any]],
    drift_result: dict[str, Any],
) -> list[dict[str, Any]]:
    breaking: list[dict[str, Any]] = []
    for issue in schema_issues:
        if issue.get("is_breaking_change"):
            breaking.append(issue)
    for issue in drift_result.get("drift_issues", []):
        if issue.get("is_breaking_change"):
            breaking.append(issue)
    return breaking


def _build_recommended_actions(
    schema_issues: list[dict[str, Any]],
    drift_result: dict[str, Any],
    quality_issues: list[dict[str, Any]],
) -> list[str]:
    actions: list[str] = []

    rename_candidates = [
        issue
        for issue in schema_issues
        if issue.get("issue_type") == "renamed_column_candidate"
    ]
    for issue in rename_candidates:
        actions.append(
            f"Confirm with the vendor whether '{issue['expected']}' was renamed to "
            f"'{issue['actual']}' and update the contract or ingestion mapping."
        )

    missing_columns = [
        issue["column"]
        for issue in schema_issues
        if issue.get("issue_type") == "missing_column"
    ]
    if missing_columns:
        actions.append(
            "Restore missing contract columns or publish a new contract version before "
            f"downstream jobs consume this feed: {', '.join(missing_columns)}."
        )

    added_columns = [
        issue["column"]
        for issue in drift_result.get("drift_issues", [])
        if issue.get("issue_type") == "added_column"
    ]
    if added_columns:
        actions.append(
            "Review newly added columns and decide whether to add them to the contract: "
            f"{', '.join(added_columns)}."
        )

    quality_failures = [
        issue for issue in quality_issues if issue.get("severity") in {"high", "critical"}
    ]
    if quality_failures:
        actions.append(
            "Investigate high-severity data quality failures and reject or quarantine "
            "rows before loading into production tables."
        )

    date_issues = [
        issue for issue in quality_issues if issue.get("issue_type") == "date_format_violation"
    ]
    if date_issues:
        actions.append(
            "Standardize date formatting with the vendor or add a parsing rule in ingestion."
        )

    if not actions:
        actions.append("No immediate action required. Continue monitoring future deliveries.")

    return actions


def _build_downstream_impact(
    schema_issues: list[dict[str, Any]],
    drift_result: dict[str, Any],
    quality_issues: list[dict[str, Any]],
) -> str:
    impacts: list[str] = []

    renamed = [
        issue for issue in schema_issues if issue.get("issue_type") == "renamed_column_candidate"
    ]
    if renamed:
        pairs = ", ".join(f"{i['expected']}->{i['actual']}" for i in renamed)
        impacts.append(
            f"Renamed columns ({pairs}) can break SQL models, dbt tests, and dashboards "
            "that reference the original names."
        )

    missing = [
        issue["column"]
        for issue in schema_issues
        if issue.get("issue_type") == "missing_column"
    ]
    if missing:
        impacts.append(
            f"Missing columns ({', '.join(missing)}) may cause pipeline failures, null "
            "join keys, and incomplete reporting."
        )

    if drift_result.get("breaking_changes_count", 0) > 0:
        impacts.append(
            "Breaking schema drift detected. Downstream consumers expecting the contract "
            "schema may fail at load time."
        )

    critical_quality = [
        issue for issue in quality_issues if issue.get("severity") in {"high", "critical"}
    ]
    if critical_quality:
        impacts.append(
            "Data quality failures can produce incorrect KPIs, revenue totals, and "
            "customer-level metrics."
        )

    if not impacts:
        return (
            "No significant downstream impact expected. The feed aligns with the contract."
        )

    return " ".join(impacts)


def generate_summary(
    schema_issues: list[dict[str, Any]],
    drift_result: dict[str, Any],
    quality_issues: list[dict[str, Any]],
    feed_name: str,
) -> dict[str, Any]:
    """Generate a structured impact summary from validation outputs.

    Args:
        schema_issues: Schema validation findings.
        drift_result: Structured drift detection result.
        quality_issues: Data quality findings.
        feed_name: Name of the incoming feed file.

    Returns:
        Structured summary dictionary for reporting.
    """
    all_severities = [issue.get("severity", "low") for issue in schema_issues]
    all_severities.extend(issue.get("severity", "low") for issue in quality_issues)
    all_severities.extend(
        issue.get("severity", "low") for issue in drift_result.get("drift_issues", [])
    )

    risk_level = _max_severity(all_severities)
    breaking_changes = _collect_breaking_changes(schema_issues, drift_result)

    only_low_added_columns = (
        drift_result.get("has_drift")
        and drift_result.get("breaking_changes_count", 0) == 0
        and all(
            issue.get("issue_type") == "added_column" and issue.get("severity") == "low"
            for issue in drift_result.get("drift_issues", [])
        )
    )

    has_critical_quality = any(
        issue.get("severity") in {"critical", "high"} for issue in quality_issues
    )

    if _has_missing_required_column(schema_issues) or _has_critical_schema_issue(schema_issues):
        overall_status = "FAIL"
    elif has_critical_quality:
        overall_status = "FAIL"
    elif schema_issues or quality_issues or drift_result.get("has_drift"):
        overall_status = "WARNING"
    else:
        overall_status = "PASS"

    if only_low_added_columns and not quality_issues and not breaking_changes:
        overall_status = "WARNING"

    rename_candidates = [
        issue
        for issue in schema_issues
        if issue.get("issue_type") == "renamed_column_candidate"
    ]
    rename_text = ""
    if rename_candidates:
        rename_text = " Likely column renames: " + ", ".join(
            f"{issue['expected']} -> {issue['actual']}" for issue in rename_candidates
        )

    issue_count = len(schema_issues) + len(quality_issues)
    breaking_count = drift_result.get("breaking_changes_count", 0)

    if overall_status == "PASS":
        executive_summary = (
            f"The '{feed_name}' feed passed contract validation with no material schema "
            "drift or data quality issues."
        )
        technical_summary = (
            "Schema, drift, and quality checks completed successfully against the contract."
        )
    else:
        executive_summary = (
            f"The '{feed_name}' feed requires attention. Found {issue_count} validation "
            f"issues and {breaking_count} breaking schema changes.{rename_text}"
        )
        technical_summary = (
            f"Risk level {risk_level}. Schema issues: {len(schema_issues)}. "
            f"Drift issues: {len(drift_result.get('drift_issues', []))}. "
            f"Quality issues: {len(quality_issues)}."
        )

    return {
        "feed_name": feed_name,
        "overall_status": overall_status,
        "risk_level": risk_level,
        "executive_summary": executive_summary,
        "technical_summary": technical_summary,
        "recommended_actions": _build_recommended_actions(
            schema_issues, drift_result, quality_issues
        ),
        "breaking_changes": breaking_changes,
        "quality_issues": quality_issues,
        "downstream_impact": _build_downstream_impact(
            schema_issues, drift_result, quality_issues
        ),
    }
