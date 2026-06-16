# Session — hotfix: /settings 500 (Jinja `domain.keys` → dict-method collision)

> **Status:** `complete`

## Origin

Owner, minutes after #977 merged: *"the settings tab gives an internal service error."* The live
`/settings` page 500'd.

## Root cause

`dashboard/templates/settings.html` iterated `domain.keys` (the scanner field holding the list of
`{constant, key}` entries). In Jinja, attribute access `domain.keys` on a **dict** resolves to the
dict's built-in **`.keys` method**, not the `"keys"` item — so `{% for k in domain.keys %}` tried to
iterate a `builtin_function_or_method` → `TypeError` → 500. Classic Jinja footgun: dict items named
`keys` / `items` / `values` collide with dict methods.

## Fix

Subscript access — `domain['keys']` — in all four spots (the two `{% for %}` loops + the `| length`
count). Subscript forces item lookup, bypassing the method. No data/scanner change; the JSON was fine.

## Why CI didn't catch it (the real lesson)

The dashboard app smoke test (`tests/unit/dashboard/test_app.py`) is **`importorskip`-guarded** and
**skips in CI** by design — CI installs only the bot's `requirements.txt`, never the dashboard's web
deps (the decoupling contract). So a **template-only** bug is invisible to CI, and my local run had
*also* skipped because the web deps weren't installed. The smoke test *does* catch this (the
`/settings` render → 200 assertion failed once deps were present) — it just never ran.

**Process fix (applied):** install the dashboard deps and run the smoke test **locally** before
pushing any `dashboard/` template change:
`python3.10 -m pip install -r dashboard/requirements.txt httpx && python3.10 -m pytest tests/unit/dashboard/`.

## Verification

- `python3.10 -m pip install -r dashboard/requirements.txt httpx` then
  `python3.10 -m pytest tests/unit/dashboard/test_app.py` → **13 passed** (`/settings` + `/access`
  both render 200). Before the fix: `TypeError` on `/settings`.

**Merge ≠ deploy:** the dashboard auto-redeploys on merge to `main`; `/settings` recovers after the
redeploy.

## 💡 Session idea (Q-0089)

**A dashboard-only CI job** (`.github/workflows/dashboard-ci.yml`, triggered on `dashboard/**` +
`scripts/scan_*` + `scripts/export_dashboard_data.py`) that installs the dashboard deps and runs
`tests/unit/dashboard/` + the scanner tests. This is the structural fix for *"CI can't see dashboard
template bugs"* — it would have caught this 500 on the original PR. Keeps the bot's CI untouched
(separate job), honoring the decoupling. Worth doing as the immediate next dashboard PR.
