"""
streamlit_app.py
----------------
Streamlit dashboard for the AI Data Contract & Schema Drift Guardian.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.pipeline.validation_pipeline import DEFAULT_CONTRACT_PATH, run_validation_pipeline
from src.reporting.report_writer import write_reports

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INCOMING_DIR = PROJECT_ROOT / "data" / "incoming"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
DEFAULT_CONTRACT = PROJECT_ROOT / DEFAULT_CONTRACT_PATH


def _resolve_incoming_files() -> list[Path]:
    if not INCOMING_DIR.exists():
        return []
    return sorted(INCOMING_DIR.glob("*.csv"))


def _status_color(status: str) -> str:
    return {
        "PASS": "green",
        "WARNING": "orange",
        "FAIL": "red",
    }.get(status, "gray")


def _issues_dataframe(result: dict) -> pd.DataFrame:
    rows = []
    for issue in result.get("schema_issues", []):
        rows.append(
            {
                "category": "schema_validation",
                "issue_type": issue.get("issue_type"),
                "severity": issue.get("severity"),
                "column": issue.get("column"),
                "message": issue.get("message"),
                "is_breaking_change": issue.get("is_breaking_change", False),
            }
        )
    for issue in result.get("drift_result", {}).get("drift_issues", []):
        rows.append(
            {
                "category": "schema_drift",
                "issue_type": issue.get("issue_type"),
                "severity": issue.get("severity"),
                "column": issue.get("column"),
                "message": issue.get("message"),
                "is_breaking_change": issue.get("is_breaking_change", False),
            }
        )
    for issue in result.get("quality_issues", []):
        rows.append(
            {
                "category": "data_quality",
                "issue_type": issue.get("issue_type"),
                "severity": issue.get("severity"),
                "column": issue.get("column"),
                "message": issue.get("message"),
                "is_breaking_change": False,
                "failed_rows_count": issue.get("failed_rows_count"),
                "failed_percentage": issue.get("failed_percentage"),
                "sample_bad_values": issue.get("sample_bad_values"),
            }
        )
    return pd.DataFrame(rows)


def _render_charts(result: dict) -> None:
    issues_df = _issues_dataframe(result)
    if issues_df.empty:
        st.info("No issues to chart for this run.")
        return

    chart_cols = st.columns(2)

    severity_counts = (
        issues_df["severity"].fillna("unknown").value_counts().reset_index()
    )
    severity_counts.columns = ["severity", "count"]
    chart_cols[0].subheader("Issues by Severity")
    chart_cols[0].bar_chart(severity_counts, x="severity", y="count")

    category_counts = issues_df["category"].value_counts().reset_index()
    category_counts.columns = ["category", "count"]
    chart_cols[1].subheader("Issues by Category")
    chart_cols[1].bar_chart(category_counts, x="category", y="count")

    null_df = pd.DataFrame(result["actual_schema"])
    if not null_df.empty and "null_count" in null_df.columns:
        st.subheader("Null Count by Column")
        null_chart = null_df[["name", "null_count"]].rename(columns={"name": "column"})
        st.bar_chart(null_chart, x="column", y="null_count")

    df = result["dataframe"]
    status_col = None
    for candidate in ("status", "order_status"):
        if candidate in df.columns:
            status_col = candidate
            break

    if status_col:
        st.subheader(f"{status_col} Distribution")
        status_counts = df[status_col].fillna("NULL").value_counts().reset_index()
        status_counts.columns = [status_col, "count"]
        st.bar_chart(status_counts, x=status_col, y="count")


def _render_contract_details(contract: dict) -> None:
    columns = contract.get("schema", {}).get("columns", [])
    quality = contract.get("quality", {})

    contract_df = pd.DataFrame(
        [
            {
                "column": col.get("name"),
                "dtype": col.get("dtype"),
                "nullable": col.get("nullable"),
                "unique": col.get("unique", False),
                "min_value": col.get("min_value"),
                "max_value": col.get("max_value"),
                "allowed_values": col.get("allowed_values"),
                "pattern": col.get("pattern"),
                "date_format": col.get("date_format"),
            }
            for col in columns
        ]
    )
    st.subheader("Expected Schema")
    st.dataframe(contract_df, use_container_width=True)

    st.subheader("Quality Thresholds")
    st.json(quality)


def main() -> None:
    st.set_page_config(
        page_title="AI Data Contract & Schema Drift Guardian",
        page_icon="🛡️",
        layout="wide",
    )
    st.title("AI Data Contract & Schema Drift Guardian")
    st.caption(
        "Validate vendor feeds against YAML contracts, detect schema drift, "
        "and review data quality issues."
    )

    incoming_files = _resolve_incoming_files()
    if not incoming_files:
        st.error(f"No CSV files found in {INCOMING_DIR}")
        return

    file_labels = [path.name for path in incoming_files]
    selected_name = st.selectbox("Select incoming CSV file", file_labels)
    selected_path = INCOMING_DIR / selected_name

    if st.button("Run Validation", type="primary"):
        with st.spinner("Running validation pipeline..."):
            result = run_validation_pipeline(
                str(selected_path),
                str(DEFAULT_CONTRACT),
            )
            report_paths = write_reports(result, output_dir=str(REPORTS_DIR))
            st.session_state["validation_result"] = result
            st.session_state["report_paths"] = report_paths

    result = st.session_state.get("validation_result")
    if not result:
        st.info("Select a CSV file and click **Run Validation** to view results.")
        return

    summary = result["impact_summary"]
    status = result["overall_status"]
    st.markdown(
        f"### Overall Status: :{_status_color(status)}[{status}] | "
        f"Risk: **{result['risk_level']}**"
    )

    metric_cols = st.columns(4)
    metric_cols[0].metric("Overall Status", status)
    metric_cols[1].metric("Risk Level", result["risk_level"])
    metric_cols[2].metric("Breaking Changes", result["breaking_changes_count"])
    metric_cols[3].metric("Total Issues", result["total_issues"])

    report_paths = st.session_state.get("report_paths", {})
    if report_paths:
        st.caption(
            f"Reports saved: `{report_paths.get('json')}`, "
            f"`{report_paths.get('markdown')}`, `{report_paths.get('csv')}`"
        )

    tabs = st.tabs(
        ["Overview", "Schema Drift", "Data Quality", "Contract Details", "Raw Data Preview"]
    )

    with tabs[0]:
        st.subheader("Executive Summary")
        st.write(summary["executive_summary"])
        st.subheader("Recommended Actions")
        for index, action in enumerate(summary["recommended_actions"], start=1):
            st.write(f"{index}. {action}")
        st.subheader("Downstream Impact")
        st.write(summary["downstream_impact"])
        _render_charts(result)

    with tabs[1]:
        st.subheader("Schema Validation Issues")
        schema_df = pd.DataFrame(result["schema_issues"])
        if schema_df.empty:
            st.success("No schema validation issues detected.")
        else:
            st.dataframe(schema_df, use_container_width=True)

        st.subheader("Schema Drift Issues")
        drift_issues = result["drift_result"].get("drift_issues", [])
        if not drift_issues:
            st.success("No schema drift detected.")
        else:
            drift_df = pd.DataFrame(drift_issues)
            if "is_breaking_change" in drift_df.columns:
                breaking_df = drift_df[drift_df["is_breaking_change"]]
                non_breaking_df = drift_df[~drift_df["is_breaking_change"]]
                st.markdown("**Breaking changes**")
                st.dataframe(breaking_df, use_container_width=True)
                st.markdown("**Non-breaking changes**")
                st.dataframe(non_breaking_df, use_container_width=True)
            else:
                st.dataframe(drift_df, use_container_width=True)

    with tabs[2]:
        quality_df = pd.DataFrame(result["quality_issues"])
        if quality_df.empty:
            st.success("No data quality issues detected.")
        else:
            display_cols = [
                col
                for col in [
                    "issue_type",
                    "severity",
                    "column",
                    "failed_rows_count",
                    "failed_percentage",
                    "message",
                    "sample_bad_values",
                ]
                if col in quality_df.columns
            ]
            st.dataframe(quality_df[display_cols], use_container_width=True)

    with tabs[3]:
        _render_contract_details(result["contract"])

    with tabs[4]:
        st.subheader("First 10 Rows")
        st.dataframe(result["dataframe"].head(10), use_container_width=True)


if __name__ == "__main__":
    main()
