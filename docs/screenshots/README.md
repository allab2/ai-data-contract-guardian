# Screenshots

This folder contains documentation images for the GitHub README.

## Generated assets (from real pipeline output)

Run the generator after validating Day 2 data:

```bash
python scripts/generate_screenshot_assets.py
```

| File | Description |
|---|---|
| `streamlit_overview.png` | Issues by severity chart (Day 2) |
| `streamlit_schema_drift.png` | Issues by category chart (Day 2) |
| `streamlit_data_quality.png` | Null count by column (Day 2) |
| `architecture.png` | Status / order_status distribution (Day 2) |
| `cli_output.png` | CLI validation summary (Day 2) |
| `markdown_report_preview.png` | Markdown report excerpt (Day 2) |

These charts are built from **actual validation results**, not mock data.

## Optional live UI captures

For additional portfolio polish, run the dashboard and capture live Streamlit tabs:

```bash
make dashboard
```

Suggested manual captures:

- Streamlit Overview tab (full page)
- Schema Drift tab (issue tables)
- Data Quality tab (failed rows and sample bad values)

Save extra PNGs here and link them from the root `README.md`.
