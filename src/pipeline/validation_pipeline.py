"""
validation_pipeline.py
----------------------
Reusable orchestration for the full data contract validation workflow.
Used by the CLI and Streamlit dashboard to avoid duplicated logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.contracts.contract_loader import load_contract
from src.drift.drift_detector import detect_drift
from src.ingestion.file_loader import load_csv
from src.profiling.schema_profiler import profile_schema
from src.summary.impact_summary_generator import generate_summary
from src.validation.data_quality_validator import validate_data_quality
from src.validation.schema_validator import validate_schema

DEFAULT_CONTRACT_PATH = "config/data_contracts/customer_orders_contract.yml"


def run_validation_pipeline(
    file_path: str,
    contract_path: str = DEFAULT_CONTRACT_PATH,
) -> dict[str, Any]:
    """Run the full validation pipeline for an incoming data file.

    Args:
        file_path: Path to the incoming CSV file.
        contract_path: Path to the YAML data contract.

    Returns:
        Structured result dictionary used by CLI, dashboard, and report writer.
    """
    df = load_csv(file_path)
    contract = load_contract(contract_path)
    actual_schema = profile_schema(df)

    schema_issues = validate_schema(actual_schema, contract)
    drift_result = detect_drift(actual_schema, contract)
    quality_issues = validate_data_quality(df, contract)
    impact_summary = generate_summary(
        schema_issues=schema_issues,
        drift_result=drift_result,
        quality_issues=quality_issues,
        feed_name=Path(file_path).name,
    )

    total_issues = (
        len(schema_issues)
        + len(drift_result.get("drift_issues", []))
        + len(quality_issues)
    )

    return {
        "feed_name": Path(file_path).name,
        "file_path": file_path,
        "contract_path": contract_path,
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
        "row_count": len(df),
        "column_count": len(df.columns),
        "actual_schema": actual_schema,
        "contract": contract,
        "schema_issues": schema_issues,
        "drift_result": drift_result,
        "quality_issues": quality_issues,
        "impact_summary": impact_summary,
        "overall_status": impact_summary["overall_status"],
        "risk_level": impact_summary["risk_level"],
        "breaking_changes_count": drift_result.get("breaking_changes_count", 0),
        "total_issues": total_issues,
        "recommended_actions": impact_summary["recommended_actions"],
        "dataframe": df,
    }
