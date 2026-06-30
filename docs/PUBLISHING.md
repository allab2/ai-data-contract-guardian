# Publishing to GitHub

Repository (live): https://github.com/allab2/ai-data-contract-guardian

---

## Status

- [x] Repository created and pushed to `main`
- [x] GitHub Actions CI passing
- [ ] GitHub Topics added (see below)
- [ ] Release tag `v1.0.0` created
- [ ] README screenshots added manually (see `docs/screenshots/README.md`)

---

## Recommended GitHub Topics

On the repository page, click **⚙️ Settings** (or the gear next to About) → **Topics**, and add:

```text
data-engineering
schema-drift
data-quality
data-contracts
python
streamlit
duckdb
pytest
data-observability
vendor-feeds
portfolio-project
```

Or via CLI:

```bash
gh repo edit allab2/ai-data-contract-guardian \
  --add-topic data-engineering,schema-drift,data-quality,data-contracts,python,streamlit,duckdb,pytest,data-observability,vendor-feeds,portfolio-project
```

---

## Create Release Tag

Tag the initial portfolio release:

```bash
git tag -a v1.0.0 -m "Initial portfolio release"
git push origin v1.0.0
```

Then create a **GitHub Release** from the tag:

1. Go to https://github.com/allab2/ai-data-contract-guardian/releases
2. Click **Draft a new release**
3. Choose tag `v1.0.0`
4. Title: `v1.0.0 — Initial Portfolio Release`
5. Paste a short summary from the README (problem, features, tech stack)
6. Publish release

Or via CLI:

```bash
gh release create v1.0.0 \
  --title "v1.0.0 — Initial Portfolio Release" \
  --notes "Local data contract validator with schema drift detection, quality checks, rule-based impact summaries, CLI, Streamlit dashboard, and CI."
```

---

## Verify CI

https://github.com/allab2/ai-data-contract-guardian/actions

CI runs on every push and pull request:

- `pytest tests/ -v`
- Day 1 pipeline (expected PASS)
- Day 2 pipeline (expected FAIL)
- Report file verification

---

## Add README screenshots

```bash
make dashboard
```

Follow [docs/screenshots/README.md](screenshots/README.md) to capture and commit dashboard images.

---

## Manual push (reference)

```bash
git remote add origin https://github.com/allab2/ai-data-contract-guardian.git
git push -u origin main
```
