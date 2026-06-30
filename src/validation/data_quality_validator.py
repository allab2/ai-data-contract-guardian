"""
data_quality_validator.py
-------------------------
Runs data-level quality checks against the incoming DataFrame using
rules from the YAML data contract.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pandas as pd

from src.validation.schema_validator import _find_rename_pairs


def _resolve_column_name(
    expected_name: str,
    df_columns: list[str],
    rename_map: dict[str, str],
) -> str | None:
    """Resolve contract column to an actual DataFrame column."""
    if expected_name in df_columns:
        return expected_name
    return rename_map.get(expected_name)


def _build_rename_map(
    expected_names: list[str],
    actual_names: list[str],
) -> dict[str, str]:
    """Map expected contract columns to likely renamed actual columns."""
    missing = [name for name in expected_names if name not in actual_names]
    unexpected = [name for name in actual_names if name not in expected_names]
    pairs = _find_rename_pairs(missing, unexpected)
    return {missing: actual for missing, actual, _ in pairs}


def _severity_for_failure_rate(failed_pct: float, threshold: float | None = None) -> str:
    if failed_pct >= 0.25:
        return "critical"
    if failed_pct >= 0.10:
        return "high"
    if threshold is not None and failed_pct > threshold:
        return "high"
    if failed_pct > 0:
        return "medium"
    return "low"


def validate_data_quality(
    df: pd.DataFrame,
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run data quality checks on the incoming DataFrame.

    Args:
        df: The incoming DataFrame.
        contract: Parsed YAML data contract.

    Returns:
        List of data quality issue dictionaries.
    """
    issues: list[dict[str, Any]] = []
    row_count = len(df)
    if row_count == 0:
        return [
            {
                "issue_type": "row_count",
                "severity": "critical",
                "column": None,
                "failed_rows_count": 0,
                "failed_percentage": 0.0,
                "threshold": contract.get("quality", {}).get("min_row_count", 1),
                "message": "Incoming feed contains zero rows.",
                "sample_bad_values": [],
            }
        ]

    quality = contract.get("quality", {})
    expected_columns = contract.get("schema", {}).get("columns", [])
    expected_names = [col["name"] for col in expected_columns]
    actual_names = list(df.columns)
    rename_map = _build_rename_map(expected_names, actual_names)

    # Dataset-level checks.
    min_row_count = quality.get("min_row_count", 1)
    if row_count < min_row_count:
        issues.append(
            {
                "issue_type": "row_count",
                "severity": "high",
                "column": None,
                "failed_rows_count": row_count,
                "failed_percentage": 1.0,
                "threshold": min_row_count,
                "message": f"Row count {row_count} is below minimum {min_row_count}.",
                "sample_bad_values": [],
            }
        )

    max_null_pct = quality.get("max_null_pct", 0.05)
    overall_null_pct = float(df.isnull().sum().sum()) / (row_count * len(df.columns))
    if overall_null_pct > max_null_pct:
        issues.append(
            {
                "issue_type": "null_percentage",
                "severity": _severity_for_failure_rate(overall_null_pct, max_null_pct),
                "column": None,
                "failed_rows_count": int(df.isnull().sum().sum()),
                "failed_percentage": round(overall_null_pct, 4),
                "threshold": max_null_pct,
                "message": (
                    f"Overall null percentage {overall_null_pct:.2%} exceeds "
                    f"contract threshold {max_null_pct:.2%}."
                ),
                "sample_bad_values": [],
            }
        )

    max_duplicate_pct = quality.get("max_duplicate_pct", 0.0)
    duplicate_count = int(df.duplicated().sum())
    duplicate_pct = duplicate_count / row_count
    if duplicate_pct > max_duplicate_pct:
        issues.append(
            {
                "issue_type": "duplicate_rows",
                "severity": "medium",
                "column": None,
                "failed_rows_count": duplicate_count,
                "failed_percentage": round(duplicate_pct, 4),
                "threshold": max_duplicate_pct,
                "message": (
                    f"Duplicate row percentage {duplicate_pct:.2%} exceeds "
                    f"threshold {max_duplicate_pct:.2%}."
                ),
                "sample_bad_values": [],
            }
        )

    for column_spec in expected_columns:
        expected_name = column_spec["name"]
        actual_name = _resolve_column_name(expected_name, actual_names, rename_map)

        if actual_name is None:
            issues.append(
                {
                    "issue_type": "column_unavailable",
                    "severity": "critical" if column_spec.get("nullable") is False else "medium",
                    "column": expected_name,
                    "failed_rows_count": row_count,
                    "failed_percentage": 1.0,
                    "threshold": None,
                    "message": (
                        f"Quality checks for '{expected_name}' were skipped because the "
                        f"column is missing from the feed."
                    ),
                    "sample_bad_values": [],
                }
            )
            continue

        if actual_name != expected_name:
            issues.append(
                {
                    "issue_type": "rename_candidate_quality_check",
                    "severity": "medium",
                    "column": expected_name,
                    "failed_rows_count": 0,
                    "failed_percentage": 0.0,
                    "threshold": None,
                    "message": (
                        f"Running quality checks for '{expected_name}' against rename "
                        f"candidate '{actual_name}'."
                    ),
                    "sample_bad_values": [],
                }
            )

        series = df[actual_name]
        nullable = column_spec.get("nullable", True)
        null_mask = series.isnull() | (series.astype(str).str.strip() == "")
        null_count = int(null_mask.sum())
        null_pct = null_count / row_count

        if not nullable and null_count > 0:
            issues.append(
                {
                    "issue_type": "required_field_null_violation",
                    "severity": "high" if null_pct > max_null_pct else "medium",
                    "column": expected_name,
                    "failed_rows_count": null_count,
                    "failed_percentage": round(null_pct, 4),
                    "threshold": 0,
                    "message": (
                        f"Column '{expected_name}' (actual: '{actual_name}') has "
                        f"{null_count} null/blank values but is required."
                    ),
                    "sample_bad_values": series[null_mask].head(5).tolist(),
                }
            )

        if column_spec.get("unique") and series.nunique(dropna=True) != series.dropna().shape[0]:
            duplicate_values = series[series.duplicated(keep=False) & series.notna()]
            dup_count = int(duplicate_values.shape[0])
            issues.append(
                {
                    "issue_type": "uniqueness_violation",
                    "severity": "high",
                    "column": expected_name,
                    "failed_rows_count": dup_count,
                    "failed_percentage": round(dup_count / row_count, 4),
                    "threshold": "unique=true",
                    "message": f"Column '{expected_name}' violates uniqueness constraint.",
                    "sample_bad_values": duplicate_values.head(5).tolist(),
                }
            )

        if "min_value" in column_spec or "max_value" in column_spec:
            numeric = pd.to_numeric(series, errors="coerce")
            min_value = column_spec.get("min_value")
            max_value = column_spec.get("max_value")

            below_min = numeric < min_value if min_value is not None else pd.Series([False] * row_count)
            above_max = numeric > max_value if max_value is not None else pd.Series([False] * row_count)
            range_mask = below_min | above_max
            range_count = int(range_mask.sum())

            if range_count > 0:
                failed_pct = range_count / row_count
                issues.append(
                    {
                        "issue_type": "range_violation",
                        "severity": _severity_for_failure_rate(failed_pct),
                        "column": expected_name,
                        "failed_rows_count": range_count,
                        "failed_percentage": round(failed_pct, 4),
                        "threshold": f"min={min_value}, max={max_value}",
                        "message": (
                            f"Column '{expected_name}' has {range_count} values outside "
                            f"allowed range [{min_value}, {max_value}]."
                        ),
                        "sample_bad_values": series[range_mask].head(5).tolist(),
                    }
                )

            if expected_name in {"quantity", "total_amount", "unit_price"}:
                negative_mask = numeric < 0
                negative_count = int(negative_mask.sum())
                if negative_count > 0:
                    failed_pct = negative_count / row_count
                    issues.append(
                        {
                            "issue_type": "negative_value",
                            "severity": "high",
                            "column": expected_name,
                            "failed_rows_count": negative_count,
                            "failed_percentage": round(failed_pct, 4),
                            "threshold": ">= 0",
                            "message": (
                                f"Column '{expected_name}' contains {negative_count} "
                                f"negative values."
                            ),
                            "sample_bad_values": series[negative_mask].head(5).tolist(),
                        }
                    )

        allowed_values = column_spec.get("allowed_values")
        if allowed_values:
            value_mask = ~series.isin(allowed_values) & series.notna()
            invalid_count = int(value_mask.sum())
            if invalid_count > 0:
                failed_pct = invalid_count / row_count
                issues.append(
                    {
                        "issue_type": "allowed_values_violation",
                        "severity": _severity_for_failure_rate(failed_pct),
                        "column": expected_name,
                        "failed_rows_count": invalid_count,
                        "failed_percentage": round(failed_pct, 4),
                        "threshold": allowed_values,
                        "message": (
                            f"Column '{expected_name}' has {invalid_count} values outside "
                            f"allowed set {allowed_values}."
                        ),
                        "sample_bad_values": series[value_mask].head(5).tolist(),
                    }
                )

        pattern = column_spec.get("pattern")
        if pattern:
            regex = re.compile(pattern)
            str_series = series.dropna().astype(str)
            invalid_mask = ~str_series.str.match(regex)
            invalid_count = int(invalid_mask.sum())
            if invalid_count > 0:
                failed_pct = invalid_count / row_count
                issues.append(
                    {
                        "issue_type": "pattern_violation",
                        "severity": "medium",
                        "column": expected_name,
                        "failed_rows_count": invalid_count,
                        "failed_percentage": round(failed_pct, 4),
                        "threshold": pattern,
                        "message": (
                            f"Column '{expected_name}' has {invalid_count} values that "
                            f"do not match pattern '{pattern}'."
                        ),
                        "sample_bad_values": str_series[invalid_mask].head(5).tolist(),
                    }
                )

        date_format = column_spec.get("date_format")
        if date_format:
            str_series = series.dropna().astype(str)
            invalid_values: list[str] = []
            for value in str_series:
                try:
                    datetime.strptime(value, date_format)
                except ValueError:
                    invalid_values.append(value)

            invalid_count = len(invalid_values)
            if invalid_count > 0:
                failed_pct = invalid_count / row_count
                issues.append(
                    {
                        "issue_type": "date_format_violation",
                        "severity": "high" if failed_pct >= 0.5 else "medium",
                        "column": expected_name,
                        "failed_rows_count": invalid_count,
                        "failed_percentage": round(failed_pct, 4),
                        "threshold": date_format,
                        "message": (
                            f"Column '{expected_name}' has {invalid_count} values that do "
                            f"not match expected date format '{date_format}'."
                        ),
                        "sample_bad_values": invalid_values[:5],
                    }
                )

    return issues
