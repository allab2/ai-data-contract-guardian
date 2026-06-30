# Architecture

This document describes how the AI Data Contract & Schema Drift Guardian is organized and how data flows through the system.

---

## Pipeline flow

```
CSV file
   │
   ▼
file_loader.load_csv()
   │
   ▼
schema_profiler.profile_schema()  ──► observed schema profile
   │
   ├── contract_loader.load_contract()  ──► YAML contract
   │
   ▼
schema_validator.validate_schema()     ──► contract compliance issues
drift_detector.detect_drift()          ──► schema change classification
data_quality_validator.validate_data_quality()  ──► value-level issues
   │
   ▼
impact_summary_generator.generate_summary()  ──► rule-based impact summary
   │
   ▼
report_writer.write_reports()  ──► JSON / Markdown / CSV
   │
   ├── CLI (main.py)
   └── Streamlit dashboard (streamlit_app.py)
```

The shared entry point is `run_validation_pipeline()` in `src/pipeline/validation_pipeline.py`. Both the CLI and dashboard call this function so orchestration logic is not duplicated.

---

## Module responsibilities

| Module | Responsibility |
|---|---|
| `src/ingestion/file_loader.py` | Load CSV files into Pandas DataFrames |
| `src/profiling/schema_profiler.py` | Extract observed column names, dtypes, null stats |
| `src/contracts/contract_loader.py` | Parse YAML data contracts |
| `src/validation/schema_validator.py` | Compare observed schema vs contract expectations |
| `src/drift/drift_detector.py` | Classify schema drift and breaking impact |
| `src/validation/data_quality_validator.py` | Run value-level quality rules from the contract |
| `src/summary/impact_summary_generator.py` | Build severity-weighted plain-English summaries |
| `src/reporting/report_writer.py` | Export JSON, Markdown, and CSV reports |
| `src/pipeline/validation_pipeline.py` | Orchestrate the full workflow |
| `src/app/streamlit_app.py` | Interactive dashboard UI |
| `main.py` | CLI with argparse |

---

## Validation vs drift detection

These are intentionally separate concerns:

### Schema validation

Answers: **Does this feed comply with the contract right now?**

Checks include:

- Missing required columns
- Unexpected new columns
- Dtype mismatches
- Non-nullable contract violations (required fields with nulls)
- Rename candidates when a missing column and a new column look similar

### Drift detection

Answers: **What kind of schema change happened, and is it breaking?**

Drift focuses on structural schema changes:

- `missing_column`
- `added_column`
- `renamed_column_candidate`
- `dtype_change`

Required-field null violations are **not** drift events. They are handled by schema validation and data quality checks.

---

## Rename-aware data quality validation

Vendors often rename columns without notice. Example: `quantity` becomes `qty`.

The quality validator:

1. Builds rename candidate pairs using the same heuristics as schema validation
2. If `quantity` is missing but `qty` is a rename candidate, min/max and negative-value checks still run against `qty`
3. Emits an informational `rename_candidate_quality_check` issue so engineers know checks ran on a substitute column

This prevents silent quality blind spots when column names change.

---

## Rename detection approach

Rename candidates are detected using:

- **Abbreviation hints** — e.g. `cust_id` → `customer_id`, `qty` → `quantity`
- **String similarity** — `difflib.SequenceMatcher`
- **Substring matching** — e.g. `status` inside `order_status`

The approach is lightweight, explainable, and requires no external AI API.

---

## Reporting layer

`src/reporting/report_writer.py` converts pipeline results into three artifacts:

| Format | File pattern | Use case |
|---|---|---|
| JSON | `{feed}_validation_report.json` | Machine-readable audit trail |
| Markdown | `{feed}_validation_report.md` | GitHub-readable sharing |
| CSV | `{feed}_issues.csv` | Spreadsheet analysis |

Reports are written to `data/reports/` on every CLI or dashboard run.

---

## Dashboard layer

`src/app/streamlit_app.py` provides:

- CSV file selection from `data/incoming/`
- One-click validation via the shared pipeline
- Status metrics (PASS / WARNING / FAIL, risk level, issue counts)
- Tabs: Overview, Schema Drift, Data Quality, Contract Details, Raw Data Preview
- Simple charts: issues by severity, issues by category, null counts, status distribution

The dashboard also saves reports to `data/reports/` after each run.

---

## Rule-based impact summaries

Impact summaries are generated without external AI APIs:

- Severity-weighted overall status and risk level
- Executive and technical summaries from templates
- Recommended actions derived from issue types
- Downstream impact narrative for renames, missing columns, and quality failures

---

## Configuration

Optional environment variables (see `.env.example`):

```bash
DEFAULT_CONTRACT_PATH=config/data_contracts/customer_orders_contract.yml
REPORTS_DIR=data/reports
```

No secrets or paid cloud services are required.

---

## Screenshots

Architecture and dashboard screenshots can be added under `docs/screenshots/` after running the dashboard locally. See `docs/screenshots/README.md` for guidance.
