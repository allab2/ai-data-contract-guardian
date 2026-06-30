"""
Tests for src.reporting.report_writer
"""

import csv
import json
from pathlib import Path

import pytest

from src.pipeline.validation_pipeline import run_validation_pipeline
from src.reporting.report_writer import (
    build_json_report,
    build_markdown_report,
    write_reports,
)

CONTRACT_PATH = "config/data_contracts/customer_orders_contract.yml"
DAY1_PATH = "data/incoming/customer_orders_day1.csv"


@pytest.fixture
def day1_result():
    return run_validation_pipeline(DAY1_PATH, CONTRACT_PATH)


def test_build_json_report_contains_required_fields(day1_result):
    payload = build_json_report(day1_result)
    assert payload["feed_name"] == "customer_orders_day1.csv"
    assert "run_timestamp" in payload
    assert payload["overall_status"] == "PASS"
    assert "schema_issues" in payload
    assert "drift_result" in payload
    assert "quality_issues" in payload
    assert "impact_summary" in payload
    assert "recommended_actions" in payload


def test_build_markdown_report_contains_sections(day1_result):
    markdown = build_markdown_report(day1_result)
    assert "## Executive Summary" in markdown
    assert "## Overall Status" in markdown
    assert "## Schema Validation" in markdown
    assert "## Schema Drift" in markdown
    assert "## Data Quality Issues" in markdown
    assert "## Recommended Actions" in markdown
    assert "## Downstream Impact" in markdown


def test_report_writer_creates_json_markdown_and_csv(day1_result, tmp_path):
    paths = write_reports(day1_result, output_dir=str(tmp_path))

    assert Path(paths["json"]).exists()
    assert Path(paths["markdown"]).exists()
    assert Path(paths["csv"]).exists()

    with open(paths["json"], encoding="utf-8") as json_file:
        payload = json.load(json_file)
    assert payload["overall_status"] == "PASS"

    markdown = Path(paths["markdown"]).read_text(encoding="utf-8")
    assert "customer_orders_day1.csv" in markdown

    with open(paths["csv"], encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert rows == [] or "category" in rows[0]
