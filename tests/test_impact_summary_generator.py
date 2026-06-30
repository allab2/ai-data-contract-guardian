"""
Tests for src.summary.impact_summary_generator
"""

from src.summary.impact_summary_generator import generate_summary


def test_summary_status_fail_when_critical_issue_exists():
    schema_issues = [
        {
            "issue_type": "missing_column",
            "severity": "critical",
            "column": "customer_id",
            "expected": "customer_id",
            "actual": None,
            "message": "Required column missing.",
            "is_breaking_change": True,
        }
    ]
    drift_result = {
        "has_drift": True,
        "breaking_changes_count": 1,
        "non_breaking_changes_count": 0,
        "drift_issues": schema_issues,
    }
    quality_issues = []

    summary = generate_summary(
        schema_issues=schema_issues,
        drift_result=drift_result,
        quality_issues=quality_issues,
        feed_name="customer_orders_day2_schema_drift.csv",
    )

    assert summary["overall_status"] == "FAIL"
    assert summary["risk_level"] == "CRITICAL"
    assert summary["breaking_changes"]
    assert summary["recommended_actions"]


def test_summary_status_pass_when_no_issues():
    drift_result = {
        "has_drift": False,
        "breaking_changes_count": 0,
        "non_breaking_changes_count": 0,
        "drift_issues": [],
    }
    summary = generate_summary([], drift_result, [], "customer_orders_day1.csv")
    assert summary["overall_status"] == "PASS"
    assert summary["risk_level"] == "LOW"
