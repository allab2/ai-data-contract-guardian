"""
Tests for src.profiling.schema_profiler
"""

import pandas as pd
import pytest
from src.profiling.schema_profiler import profile_schema


@pytest.fixture
def sample_df():
    """Create a small DataFrame for testing."""
    return pd.DataFrame(
        {
            "order_id": [1, 2, 3],
            "customer_name": ["Alice", "Bob", None],
            "amount": [10.5, 20.0, 30.75],
        }
    )


def test_profile_returns_all_columns(sample_df):
    """Profile should return one entry per column."""
    profile = profile_schema(sample_df)
    assert len(profile) == 3
    column_names = [col["name"] for col in profile]
    assert "order_id" in column_names
    assert "customer_name" in column_names
    assert "amount" in column_names


def test_profile_detects_nulls(sample_df):
    """Profile should correctly count null values."""
    profile = profile_schema(sample_df)
    name_col = next(col for col in profile if col["name"] == "customer_name")
    assert name_col["null_count"] == 1
    assert name_col["null_pct"] == pytest.approx(1 / 3, abs=0.01)


def test_profile_detects_dtypes(sample_df):
    """Profile should report correct Pandas dtypes."""
    profile = profile_schema(sample_df)
    order_col = next(col for col in profile if col["name"] == "order_id")
    assert order_col["dtype"] == "int64"
    amount_col = next(col for col in profile if col["name"] == "amount")
    assert amount_col["dtype"] == "float64"


# TODO: Add tests for unique_count accuracy
# TODO: Add tests for sample_values content
# TODO: Add tests for empty DataFrame edge case
# TODO: Add tests for DataFrame with all nulls in a column
