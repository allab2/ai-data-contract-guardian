"""
Tests for src.validation.schema_validator
"""

import pytest

from src.contracts.contract_loader import load_contract
from src.validation.schema_validator import validate_schema

CONTRACT_PATH = "config/data_contracts/customer_orders_contract.yml"


@pytest.fixture
def contract():
    return load_contract(CONTRACT_PATH)


def _profile_from_columns(columns: dict[str, str]) -> list[dict]:
    return [
        {
            "name": name,
            "dtype": dtype,
            "null_count": 0,
            "null_pct": 0.0,
            "unique_count": 1,
            "sample_values": [],
        }
        for name, dtype in columns.items()
    ]


def test_missing_required_column_detection(contract):
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
    issues = validate_schema(actual_schema, contract)
    missing = [issue for issue in issues if issue["issue_type"] == "missing_column"]
    assert any(issue["column"] == "customer_id" for issue in missing)
    assert any(issue["severity"] == "critical" for issue in missing)


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
    issues = validate_schema(actual_schema, contract)
    unexpected = [issue for issue in issues if issue["issue_type"] == "unexpected_column"]
    assert any(issue["column"] == "region" for issue in unexpected)


def test_rename_candidate_detection(contract):
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
            "discount_pct": "float64",
            "region": "object",
        }
    )
    issues = validate_schema(actual_schema, contract)
    rename_issues = [
        issue for issue in issues if issue["issue_type"] == "renamed_column_candidate"
    ]
    renamed_pairs = {(issue["expected"], issue["actual"]) for issue in rename_issues}
    assert ("customer_id", "cust_id") in renamed_pairs
    assert ("quantity", "qty") in renamed_pairs
    assert ("status", "order_status") in renamed_pairs
