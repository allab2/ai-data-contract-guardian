"""
Tests for src.validation.data_quality_validator
"""

import pandas as pd
import pytest

from src.contracts.contract_loader import load_contract
from src.validation.data_quality_validator import validate_data_quality

CONTRACT_PATH = "config/data_contracts/customer_orders_contract.yml"


@pytest.fixture
def contract():
    return load_contract(CONTRACT_PATH)


def test_invalid_allowed_values_detection(contract):
    df = pd.DataFrame(
        {
            "order_id": [1, 2],
            "customer_id": ["C001", "C002"],
            "customer_name": ["Alice", "Bob"],
            "order_date": ["2025-06-01", "2025-06-01"],
            "product_name": ["Widget", "Gadget"],
            "quantity": [1, 2],
            "unit_price": [10.0, 20.0],
            "total_amount": [10.0, 40.0],
            "status": ["completed", "done"],
        }
    )
    issues = validate_data_quality(df, contract)
    allowed_issues = [
        issue for issue in issues if issue["issue_type"] == "allowed_values_violation"
    ]
    assert allowed_issues
    assert allowed_issues[0]["column"] == "status"
    assert "done" in allowed_issues[0]["sample_bad_values"]


def test_min_max_failure_detection(contract):
    df = pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "customer_id": ["C001", "C002", "C003"],
            "customer_name": ["Alice", "Bob", "Carol"],
            "order_date": ["2025-06-01", "2025-06-01", "2025-06-01"],
            "product_name": ["Widget", "Gadget", "Widget"],
            "quantity": [-1, 0, 999],
            "unit_price": [10.0, 20.0, 5.0],
            "total_amount": [10.0, 0.0, 4995.0],
            "status": ["completed", "completed", "completed"],
        }
    )
    issues = validate_data_quality(df, contract)
    range_issues = [issue for issue in issues if issue["issue_type"] == "range_violation"]
    assert any(issue["column"] == "quantity" for issue in range_issues)
    negative_issues = [issue for issue in issues if issue["issue_type"] == "negative_value"]
    assert any(issue["column"] == "quantity" for issue in negative_issues)


def test_date_format_violation_detection(contract):
    df = pd.DataFrame(
        {
            "order_id": [1, 2],
            "customer_id": ["C001", "C002"],
            "customer_name": ["Alice", "Bob"],
            "order_date": ["06/02/2025", "2025-06-02"],
            "product_name": ["Widget", "Gadget"],
            "quantity": [1, 2],
            "unit_price": [10.0, 20.0],
            "total_amount": [10.0, 40.0],
            "status": ["completed", "completed"],
        }
    )
    issues = validate_data_quality(df, contract)
    date_issues = [issue for issue in issues if issue["issue_type"] == "date_format_violation"]
    assert date_issues
    assert date_issues[0]["column"] == "order_date"
