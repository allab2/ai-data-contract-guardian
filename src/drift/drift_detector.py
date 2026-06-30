"""
drift_detector.py
-----------------
Detects schema drift by comparing the observed schema profile against
the contract-defined expected schema.
"""

from __future__ import annotations

from typing import Any

from src.validation.schema_validator import (
    _dtypes_compatible,
    _find_rename_pairs,
    _is_required_column,
    _profile_lookup,
)


def classify_breaking_change(issue: dict[str, Any]) -> bool:
    """Determine whether a drift issue is a breaking change."""
    if issue.get("is_breaking_change") is not None:
        return bool(issue["is_breaking_change"])

    issue_type = issue.get("issue_type", "")
    severity = issue.get("severity", "low")

    if issue_type == "missing_column":
        return severity == "critical"
    if issue_type == "renamed_column_candidate":
        return severity in {"high", "critical"}
    if issue_type == "dtype_change":
        return severity in {"high", "critical"}
    if issue_type == "added_column":
        return severity in {"medium", "high", "critical"}
    return False


def detect_drift(
    actual_schema: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Detect schema drift between observed schema and contract expectations.

    Args:
        actual_schema: Observed schema profile from ``profile_schema``.
        contract: Parsed YAML data contract.

    Returns:
        Structured drift result with counts and issue details.
    """
    expected_columns = contract.get("schema", {}).get("columns", [])
    expected_names = [col["name"] for col in expected_columns]
    actual_names = [col["name"] for col in actual_schema]
    actual_by_name = _profile_lookup(actual_schema)

    expected_set = set(expected_names)
    actual_set = set(actual_names)

    missing_columns = [name for name in expected_names if name not in actual_set]
    unexpected_columns = [name for name in actual_names if name not in expected_set]
    rename_pairs = _find_rename_pairs(missing_columns, unexpected_columns)

    rename_missing = {missing for missing, _, _ in rename_pairs}
    rename_unexpected = {actual for _, actual, _ in rename_pairs}

    drift_issues: list[dict[str, Any]] = []

    for missing, actual_name, score in rename_pairs:
        expected_spec = next(col for col in expected_columns if col["name"] == missing)
        required = _is_required_column(expected_spec)
        drift_issues.append(
            {
                "issue_type": "renamed_column_candidate",
                "severity": "high" if required else "medium",
                "column": missing,
                "expected": missing,
                "actual": actual_name,
                "message": (
                    f"Possible rename detected: '{missing}' -> '{actual_name}' "
                    f"(similarity={score:.2f})."
                ),
                "is_breaking_change": required,
            }
        )

    for missing in missing_columns:
        if missing in rename_missing:
            continue
        expected_spec = next(col for col in expected_columns if col["name"] == missing)
        required = _is_required_column(expected_spec)
        drift_issues.append(
            {
                "issue_type": "missing_column",
                "severity": "critical" if required else "medium",
                "column": missing,
                "expected": missing,
                "actual": None,
                "message": f"Contract column '{missing}' is absent from the feed.",
                "is_breaking_change": required,
            }
        )

    for unexpected in unexpected_columns:
        if unexpected in rename_unexpected:
            continue
        actual_col = actual_by_name[unexpected]
        has_nulls = actual_col.get("null_count", 0) > 0
        drift_issues.append(
            {
                "issue_type": "added_column",
                "severity": "low" if has_nulls else "medium",
                "column": unexpected,
                "expected": None,
                "actual": unexpected,
                "message": f"New column '{unexpected}' is not defined in the contract.",
                "is_breaking_change": False,
            }
        )

    for expected_spec in expected_columns:
        name = expected_spec["name"]
        actual_name = name

        if name not in actual_by_name:
            for missing, candidate, _ in rename_pairs:
                if missing == name:
                    actual_name = candidate
                    break
            else:
                continue

        actual_col = actual_by_name[actual_name]
        required = _is_required_column(expected_spec)

        if not _dtypes_compatible(expected_spec.get("dtype", ""), actual_col["dtype"]):
            drift_issues.append(
                {
                    "issue_type": "dtype_change",
                    "severity": "high" if required else "medium",
                    "column": actual_name,
                    "expected": expected_spec.get("dtype"),
                    "actual": actual_col["dtype"],
                    "message": (
                        f"Dtype drift on '{actual_name}': expected "
                        f"'{expected_spec.get('dtype')}', found '{actual_col['dtype']}'."
                    ),
                    "is_breaking_change": required,
                }
            )

    breaking_count = sum(1 for issue in drift_issues if classify_breaking_change(issue))
    non_breaking_count = len(drift_issues) - breaking_count

    return {
        "has_drift": len(drift_issues) > 0,
        "breaking_changes_count": breaking_count,
        "non_breaking_changes_count": non_breaking_count,
        "drift_issues": drift_issues,
    }
