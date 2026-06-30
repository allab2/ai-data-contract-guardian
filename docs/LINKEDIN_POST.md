# LinkedIn Post Draft

Copy, personalize, and post when ready.

---

## Post

I built a local data engineering tool to catch vendor feed problems before they break downstream pipelines.

**AI Data Contract & Schema Drift Guardian** validates incoming CSV feeds against YAML-based data contracts, detects breaking schema drift, runs data quality checks, and generates rule-based impact summaries for data engineers.

Why this matters: vendor files often change silently — columns get renamed, types shift, required fields go missing, and bad values slip through. That leads to failed loads, wrong dashboards, and hours of debugging.

What it does:
- Contract validation against version-controlled YAML schemas
- Schema drift detection with breaking vs non-breaking classification
- Rename-aware data quality checks (e.g. `quantity` → `qty`)
- JSON, Markdown, and CSV report export
- CLI + Streamlit dashboard
- GitHub Actions CI with pytest

Built with Python, Pandas, DuckDB, Streamlit, and Pytest. Fully local — no paid cloud services or external AI APIs.

Repo: https://github.com/allab2/ai-data-contract-guardian

If you work with vendor feeds or data contracts, I'd love your feedback.

#DataEngineering #Python #DataQuality #SchemaDrift #DataContracts #Streamlit #Pytest #OpenSource #PortfolioProject #AnalyticsEngineering

---

## Shorter variant (if character limit matters)

Shipped a portfolio project: **AI Data Contract & Schema Drift Guardian** — validates vendor CSV feeds against YAML contracts, detects breaking schema drift, runs quality checks, and exports impact reports. Python · Pandas · DuckDB · Streamlit · Pytest. Local, no-cost stack.

https://github.com/allab2/ai-data-contract-guardian

#DataEngineering #DataQuality #SchemaDrift #Python
