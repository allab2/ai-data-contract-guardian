# Screenshots

This folder holds **real screenshots** for the GitHub README and portfolio. Do not commit fake or AI-generated images — only captures from your local environment.

Repository: https://github.com/allab2/ai-data-contract-guardian

---

## How to capture screenshots

### 1. Start the dashboard

```bash
cd ai-data-contract-guardian
source venv/bin/activate   # if not already active
make dashboard
```

Streamlit opens at `http://localhost:8501`.

### 2. Run validation on Day 2 (drifted feed)

1. In the file dropdown, select **`customer_orders_day2_schema_drift.csv`**
2. Click **Run Validation**
3. Wait for status metrics and tabs to populate

Day 2 shows the richest set of schema drift and quality issues for portfolio screenshots.

### 3. Capture each required tab

Use your OS screenshot tool (macOS: `Cmd + Shift + 4`).

| Save as | What to capture |
|---|---|
| `dashboard_overview.png` | **Overview** tab — status metrics, executive summary, recommended actions, charts |
| `schema_drift.png` | **Schema Drift** tab — schema validation + drift issue tables (breaking vs non-breaking) |
| `data_quality.png` | **Data Quality** tab — quality issues with failed row counts and sample bad values |
| `contract_details.png` | **Contract Details** tab — expected schema and quality thresholds |
| `raw_data_preview.png` | **Raw Data Preview** tab — first 10 rows of the selected CSV |
| `cli_day2_output.png` | Terminal output from `make run-day2` (full validation report) |
| `markdown_report_preview.png` | Open `data/reports/customer_orders_day2_schema_drift_validation_report.md` in your editor or GitHub preview |

Save all PNG files in this folder: `docs/screenshots/`

### 4. Verify README links

After saving, confirm images render in the root `README.md` **Dashboard Preview** section on GitHub.

---

## Optional: pipeline-generated chart assets

These are **supplementary** chart renders from real Day 2 validation output (not Streamlit UI captures):

```bash
python scripts/generate_screenshot_assets.py
# or
make screenshots
```

| File | Description |
|---|---|
| `streamlit_overview.png` | Issues by severity (chart) |
| `streamlit_schema_drift.png` | Issues by category (chart) |
| `streamlit_data_quality.png` | Null counts (text render) |
| `cli_output.png` | CLI summary render (Day 2) |

Use the manual tab captures above for primary README portfolio images.

---

## Checklist before publishing README screenshots

- [ ] `dashboard_overview.png`
- [ ] `schema_drift.png`
- [ ] `data_quality.png`
- [ ] `contract_details.png`
- [ ] `raw_data_preview.png`
- [ ] `cli_day2_output.png`
- [ ] `markdown_report_preview.png`
- [ ] Committed and pushed to `main`
- [ ] Verified on https://github.com/allab2/ai-data-contract-guardian
