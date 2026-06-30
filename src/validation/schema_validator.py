"""
schema_validator.py
-------------------
Validates the observed schema profile against the expected schema
defined in a YAML data contract.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

# Common vendor abbreviations mapped to contract column names.
_ABBREVIATION_HINTS: dict[str, str] = {
    "cust_id": "customer_id",
    "qty": "quantity",
    "order_status": "status",
}


def _normalize_dtype(dtype: str) -> str:
    """Normalize pandas dtype strings for comparison."""
    dtype = dtype.lower()
    if dtype in {"int32", "int64", "integer"}:
        return "int64"
    if dtype in {"float32", "float64", "double"}:
        return "float64"
    if dtype in {"object", "string", "str"}:
        return "object"
    if dtype in {"bool", "boolean"}:
        return "bool"
    return dtype


def _dtypes_compatible(expected: str, actual: str) -> bool:
    """Return True when observed dtype is compatible with the contract."""
    expected_norm = _normalize_dtype(expected)
    actual_norm = _normalize_dtype(actual)
    if expected_norm == actual_norm:
        return True
    # Allow int -> float promotion without treating it as breaking.
    if expected_norm == "float64" and actual_norm == "int64":
        return True
    return False


def _rename_similarity(expected: str, actual: str) -> float:
    """Score how likely two column names represent a rename."""
    expected_key = expected.lower()
    actual_key = actual.lower()

    if _ABBREVIATION_HINTS.get(actual_key) == expected_key:
        return 0.95
    if _ABBREVIATION_HINTS.get(expected_key) == actual_key:
        return 0.95

    expected_compact = expected_key.replace("_", "")
    actual_compact = actual_key.replace("_", "")

    if expected_compact in actual_compact or actual_compact in expected_compact:
        return 0.85

    return SequenceMatcher(None, expected_key, actual_key).ratio()


def _find_rename_pairs(
    missing_columns: list[str],
    unexpected_columns: list[str],
    threshold: float = 0.72,
) -> list[tuple[str, str, float]]:
    """Match missing/unexpected columns that may be renames."""
    pairs: list[tuple[str, str, float]] = []
    used_unexpected: set[str] = set()

    for missing in missing_columns:
        best_match: tuple[str, float] | None = None
        for unexpected in unexpected_columns:
            if unexpected in used_unexpected:
                continue
            score = _rename_similarity(missing, unexpected)
            if score >= threshold and (best_match is None or score > best_match[1]):
                best_match = (unexpected, score)

        if best_match is not None:
            unexpected_name, score = best_match
            pairs.append((missing, unexpected_name, score))
            used_unexpected.add(unexpected_name)

    return pairs


def _profile_lookup(actual_schema: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {col["name"]: col for col in actual_schema}


def _is_required_column(column_spec: dict[str, Any]) -> bool:
    return column_spec.get("nullable", True) is False


def validate_schema(
    actual_schema: list[dict[str, Any]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare profiled actual schema against the YAML contract.

    Args:
        actual_schema: Observed schema profile from ``profile_schema``.
        contract: Parsed YAML data contract.

    Returns:
        List of schema validation issue dictionaries.
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

    issues: list[dict[str, Any]] = []

    for missing, actual_name, score in rename_pairs:
        expected_spec = next(col for col in expected_columns if col["name"] == missing)
        actual_col = actual_by_name[actual_name]
        required = _is_required_column(expected_spec)
        issues.append(
            {
                "issue_type": "renamed_column_candidate",
                "severity": "high" if required else "medium",
                "column": missing,
                "expected": missing,
                "actual": actual_name,
                "message": (
                    f"Required column '{missing}' is missing; '{actual_name}' was added "
                    f"and looks like a rename candidate (similarity={score:.2f})."
                    if required
                    else f"Column '{missing}' is missing; '{actual_name}' may be a rename."
                ),
                "is_breaking_change": required,
            }
        )

        if not _dtypes_compatible(expected_spec.get("dtype", ""), actual_col["dtype"]):
            issues.append(
                {
                    "issue_type": "dtype_mismatch",
                    "severity": "high" if required else "medium",
                    "column": actual_name,
                    "expected": expected_spec.get("dtype"),
                    "actual": actual_col["dtype"],
                    "message": (
                        f"Rename candidate '{actual_name}' has dtype '{actual_col['dtype']}', "
                        f"expected '{expected_spec.get('dtype')}' for '{missing}'."
                    ),
                    "is_breaking_change": required,
                }
            )

        if required and actual_col.get("null_count", 0) > 0:
            issues.append(
                {
                    "issue_type": "non_nullable_contract_violation",
                    "severity": "high",
                    "column": actual_name,
                    "expected": "nullable=false",
                    "actual": f"null_pct={actual_col.get('null_pct', 0):.2%}",
                    "message": (
                        f"Rename candidate '{actual_name}' for required column '{missing}' "
                        f"contains null values."
                    ),
                    "is_breaking_change": True,
                }
            )

    for missing in missing_columns:
        if missing in rename_missing:
            continue
        expected_spec = next(col for col in expected_columns if col["name"] == missing)
        required = _is_required_column(expected_spec)
        issues.append(
            {
                "issue_type": "missing_column",
                "severity": "critical" if required else "medium",
                "column": missing,
                "expected": missing,
                "actual": None,
                "message": (
                    f"Required column '{missing}' is missing from the incoming feed."
                    if required
                    else f"Optional column '{missing}' is missing from the incoming feed."
                ),
                "is_breaking_change": required,
            }
        )

    for unexpected in unexpected_columns:
        if unexpected in rename_unexpected:
            continue
        actual_col = actual_by_name[unexpected]
        has_nulls = actual_col.get("null_count", 0) > 0
        issues.append(
            {
                "issue_type": "unexpected_column",
                "severity": "low" if has_nulls else "medium",
                "column": unexpected,
                "expected": None,
                "actual": unexpected,
                "message": (
                    f"Unexpected column '{unexpected}' was added to the feed."
                    + (" Column contains null values." if has_nulls else "")
                ),
                "is_breaking_change": False,
            }
        )

    for expected_spec in expected_columns:
        name = expected_spec["name"]
        if name not in actual_by_name:
            continue

        actual_col = actual_by_name[name]
        required = _is_required_column(expected_spec)

        if not _dtypes_compatible(expected_spec.get("dtype", ""), actual_col["dtype"]):
            issues.append(
                {
                    "issue_type": "dtype_mismatch",
                    "severity": "high" if required else "medium",
                    "column": name,
                    "expected": expected_spec.get("dtype"),
                    "actual": actual_col["dtype"],
                    "message": (
                        f"Column '{name}' has dtype '{actual_col['dtype']}', "
                        f"expected '{expected_spec.get('dtype')}'."
                    ),
                    "is_breaking_change": required,
                }
            )

        if required and actual_col.get("null_count", 0) > 0:
            issues.append(
                {
                    "issue_type": "non_nullable_contract_violation",
                    "severity": "high",
                    "column": name,
                    "expected": "nullable=false",
                    "actual": f"null_pct={actual_col.get('null_pct', 0):.2%}",
                    "message": (
                        f"Required column '{name}' contains null values "
                        f"({actual_col.get('null_count', 0)} rows)."
                    ),
                    "is_breaking_change": True,
                }
            )

    return issues
