# Publishing to GitHub

The repository is initialized and committed locally. Complete these steps once to publish.

## 1. Authenticate GitHub CLI

```bash
gh auth login
```

Follow the prompts (browser or token).

## 2. Create the remote repository and push

```bash
cd ai-data-contract-guardian

gh repo create ai-data-contract-guardian \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Local data contract validator with schema drift detection, quality checks, and rule-based impact summaries."
```

If the repo name is already taken, pick another name and update badge URLs in `README.md`.

## 3. Verify CI

After push, open:

```
https://github.com/allab2/ai-data-contract-guardian/actions
```

The CI workflow should run pytest and both Day 1 / Day 2 pipelines.

## 4. Optional polish

```bash
make screenshots   # regenerate docs/screenshots from Day 2 pipeline
make dashboard     # capture live Streamlit UI screenshots manually
```

## Manual push (without gh)

If you prefer the GitHub website:

1. Create a new empty repo named `ai-data-contract-guardian` on GitHub.
2. Run:

```bash
git remote add origin https://github.com/allab2/ai-data-contract-guardian.git
git push -u origin main
```
