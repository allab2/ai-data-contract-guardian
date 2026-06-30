"""
Tests for src.pipeline.validation_pipeline
"""

from src.pipeline.validation_pipeline import run_validation_pipeline

CONTRACT_PATH = "config/data_contracts/customer_orders_contract.yml"
DAY1_PATH = "data/incoming/customer_orders_day1.csv"
DAY2_PATH = "data/incoming/customer_orders_day2_schema_drift.csv"


def test_pipeline_returns_pass_for_day1():
    result = run_validation_pipeline(DAY1_PATH, CONTRACT_PATH)
    assert result["overall_status"] == "PASS"
    assert result["risk_level"] == "LOW"
    assert result["breaking_changes_count"] == 0
    assert result["total_issues"] == 0
    assert "impact_summary" in result
    assert "dataframe" in result


def test_pipeline_returns_fail_for_day2():
    result = run_validation_pipeline(DAY2_PATH, CONTRACT_PATH)
    assert result["overall_status"] == "FAIL"
    assert result["risk_level"] == "CRITICAL"
    assert result["breaking_changes_count"] >= 1
    assert result["total_issues"] > 0
    assert len(result["schema_issues"]) > 0
    assert len(result["quality_issues"]) > 0
