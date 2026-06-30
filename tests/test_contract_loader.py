"""
Tests for src.contracts.contract_loader
"""

import pytest
from src.contracts.contract_loader import (
    load_contract,
    get_expected_columns,
    get_quality_thresholds,
)

CONTRACT_PATH = "config/data_contracts/customer_orders_contract.yml"


def test_load_contract_returns_dict():
    """Loading a valid YAML contract should return a dictionary."""
    contract = load_contract(CONTRACT_PATH)
    assert isinstance(contract, dict)
    assert "contract" in contract
    assert "schema" in contract


def test_load_contract_file_not_found():
    """Loading a nonexistent contract should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_contract("nonexistent/path/contract.yml")


def test_get_expected_columns():
    """Expected columns should be a non-empty list of dicts."""
    contract = load_contract(CONTRACT_PATH)
    columns = get_expected_columns(contract)
    assert isinstance(columns, list)
    assert len(columns) > 0
    assert all("name" in col for col in columns)
    assert all("dtype" in col for col in columns)


def test_get_quality_thresholds():
    """Quality thresholds should contain expected keys."""
    contract = load_contract(CONTRACT_PATH)
    thresholds = get_quality_thresholds(contract)
    assert isinstance(thresholds, dict)
    assert "min_row_count" in thresholds
    assert "max_null_pct" in thresholds


# TODO: Add tests for malformed YAML contracts
# TODO: Add tests for contracts missing optional fields
# TODO: Add tests for contract version validation
