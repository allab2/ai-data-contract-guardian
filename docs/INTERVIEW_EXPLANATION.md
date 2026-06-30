# Interview Explanation Guide

Quick talking points for explaining **AI Data Contract & Schema Drift Guardian** in interviews.

Repository: https://github.com/allab2/ai-data-contract-guardian

---

## 30-second explanation

"I built a local Python tool that validates vendor data feeds against YAML data contracts. It profiles each incoming file, checks schema compliance, detects breaking schema drift, runs data quality rules, and produces plain-English impact summaries plus JSON and Markdown reports. It's modular, fully tested with pytest, and includes a Streamlit dashboard and GitHub Actions CI — all without paid cloud services."

---

## 60-second explanation

"Data teams often receive vendor files that change without notice — columns get renamed, types shift, and quality degrades. I built a guardrail that runs before data hits production pipelines.

The tool loads a CSV, profiles its schema, and compares it to a YAML contract that defines expected columns, types, nullability, allowed values, and quality thresholds. A separate drift module classifies structural changes as breaking or non-breaking. Quality checks are rename-aware — if `quantity` is missing but `qty` looks like a rename, min/max checks still run.

Results feed a rule-based summary generator that outputs PASS/WARNING/FAIL status, recommended actions, and downstream impact. There's a CLI, report export, Streamlit UI, and CI that runs Day 1 and Day 2 sample feeds."

---

## Technical deep dive

### Pipeline flow

1. **Ingest** — CSV loaded via Pandas
2. **Profile** — observed schema (dtypes, null counts, sample values)
3. **Contract load** — YAML parsed with PyYAML
4. **Schema validation** — compliance vs contract
5. **Drift detection** — structural change classification
6. **Data quality** — value-level rules from contract
7. **Impact summary** — severity-weighted rule-based narrative
8. **Report export** — JSON, Markdown, CSV

Shared orchestration: `run_validation_pipeline()` — used by CLI and Streamlit.

### Key modules

| Module | Role |
|---|---|
| `schema_validator.py` | Contract compliance |
| `drift_detector.py` | Schema change types + breaking impact |
| `data_quality_validator.py` | Nulls, ranges, allowed values, dates |
| `impact_summary_generator.py` | Executive + technical summaries |
| `report_writer.py` | Persist results |

---

## Design decisions

### Why validation and drift detection are separate

- **Validation** answers: *Does this file comply with the contract today?*
- **Drift detection** answers: *What kind of schema change happened, and is it breaking?*

Example: a required column with nulls is a **contract violation** and **quality issue**, not schema drift. Drift focuses on missing columns, added columns, rename candidates, and dtype changes.

This separation keeps each module focused and easier to test and explain.

### How rename detection works

Rename candidates use three lightweight heuristics:

1. **Abbreviation hints** — `cust_id` → `customer_id`, `qty` → `quantity`
2. **Substring matching** — `status` inside `order_status`
3. **String similarity** — `difflib.SequenceMatcher` ratio threshold

No ML, no external API — explainable and fast.

### Why data quality checks follow rename candidates

If a vendor renames `quantity` to `qty`, strict column-name matching would skip min/max checks entirely. The quality validator maps rename candidates back to contract columns so range and negative-value rules still apply, with an informational issue noting the substitute column.

### Why rule-based summaries (not LLM)

For a portfolio v1, rule-based templates are:

- Deterministic and testable
- Free and local
- Interview-friendly — you own the logic

Severity-weighted rules drive status, risk level, recommended actions, and downstream impact text.

---

## What I would improve in production

| Area | Production enhancement |
|---|---|
| Orchestration | Airflow / Dagster scheduled validation on landing-zone files |
| Contracts | Contract registry with versioning and approval workflow |
| Storage | DuckDB or warehouse tables for historical drift trends |
| Alerting | Slack/PagerDuty on breaking changes |
| Scale | Spark/DuckDB distributed profiling for large files |
| Testing | dbt tests aligned with contract definitions |
| Summaries | Optional Ollama/local LLM layer on top of structured findings |
| Deployment | Containerized service or Lambda on S3 event triggers |

---

## Future enhancements (talk track)

- **Airflow** — daily validation task after vendor file lands in S3
- **dbt** — contract rules mirrored as dbt tests on staging models
- **Ollama** — richer natural-language summaries from structured JSON findings
- **Cloud** — serverless validator triggered by object storage events (still contract-driven)
- **Great Expectations** — advanced statistical profiling and custom expectations
- **Multi-format** — Parquet, JSON, API feeds

---

## Sample walkthrough (Day 2 demo)

1. Run `make run-day2`
2. Show **FAIL** status, 3 breaking rename candidates
3. Point to quality issues: invalid status `done`, date format drift, negative quantity
4. Open Markdown report in `data/reports/`
5. Open Streamlit dashboard for interactive exploration

This demo shows both **schema** and **value-level** problems in one pass.
