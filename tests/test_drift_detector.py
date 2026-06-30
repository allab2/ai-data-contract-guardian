"""
Tests for src.drift.drift_detector
"""

import pytest

from src.contracts.contract_loader import load_contract
from src.drift.drift_detector import classify_breaking_change, detect_drift

CONTRACT_PATH = "config/data_contracts/customer_orders_contract.yml"


@pytest.fixture
def contract():
    return load_contract(CONTRACT_PATH)


def _profile_from_columns(columns: dict[str, str], null_counts: dict[str, int] | None = None) -> list[dict]:
    null_counts = null_counts or {}
    return [
        {
            "name": name,
            "dtype": dtype,
            "null_count": null_counts.get(name, 0),
            "null_pct": null_counts.get(name, 0) / 10,
            "unique_count": 1,
            "sample_values": [],
        }
        for name, dtype in columns.items()
    ]


def test_detect_drift_returns_structured_result(contract):
    actual_schema = _profile_from_columns({"order_id": "int64", "customer_id": "object"})
    result = detect_drift(actual_schema, contract)
    assert isinstance(result, dict)
    assert "has_drift" in result
    assert "breaking_changes_count" in result
    assert "drift_issues" in result


def test_missing_required_column_is_breaking(contract):
    actual_schema = _profile_from_columns(
        {
            "order_id": "int64",
            "customer_name": "object",
            "order_date": "object",
            "product_name": "object",
            "quantity": "int64",
            "unit_price": "float64",
            "total_amount": "float64",
            "status": "object",
        }
    )
    result = detect_drift(actual_schema, contract)
    missing = [
        issue for issue in result["drift_issues"] if issue["issue_type"] == "missing_column"
    ]
    assert missing
    assert classify_breaking_change(missing[0]) is True
    assert missing[0]["severity"] == "critical"


def test_rename_candidate_is_high_breaking_change(contract):
    actual_schema = _profile_from_columns(
        {
            "order_id": "int64",
            "cust_id": "object",
            "customer_name": "object",
            "order_date": "object",
            "product_name": "object",
            "qty": "int64",
            "unit_price": "float64",
            "total_amount": "float64",
            "order_status": "object",
        }
    )
    result = detect_drift(actual_schema, contract)
    rename_issues = [
        issue for issue in result["drift_issues"] if issue["issue_type"] == "renamed_column_candidate"
    ]
    assert rename_issues
    assert all(classify_breaking_change(issue) for issue in rename_issues)
    assert result["breaking_changes_count"] >= 1


def test_added_column_detection(contract):
    actual_schema = _profile_from_columns(
        {
            "order_id": "int64",
            "customer_id": "object",
            "customer_name": "object",
            "order_date": "object",
            "product_name": "object",
            "quantity": "int64",
            "unit_price": "float64",
            "total_amount": "float64",
            "status": "object",
            "region": "object",
        }
    )
    result = detect_drift(actual_schema, contract)
    added = [issue for issue in result["drift_issues"] if issue["issue_type"] == "added_column"]
    assert any(issue["column"] == "region" for issue in added)
    assert classify_breaking_change(added[0]) is False


def test_no_drift_for_matching_schema(contract):
    actual_schema = _profile_from_columns(
        {
            "order_id": "int64",
            "customer_id": "object",
            "customer_name": "object",
            "order_date": "object",
            "product_name": "object",
            "quantity": "int64",
            "unit_price": "float64",
            "total_amount": "float64",
            "status": "object",
        }
    )
    result = detect_drift(actual_schema, contract)
    assert result["has_drift"] is False
    assert result["breaking_changes_count"] == 0
