# Dashboard ideas + dynamic data planning session

> **Status:** `plan` — produced repo-grounded dashboard website/dynamic-data plan only; no runtime changes.

## Summary

Created `docs/planning/dashboard-website-ideas-and-dynamic-data-plan.md`, mapping the current dashboard routes, data trust levels, dynamic data strategy, command/button metadata reliability gap, security model, phased feature roadmap, required bot-side foundations, and first safe implementation PRs.

## Context-delta

### needed-not-pointed

- `disbot/control_api.py` was needed to verify the private control API is merged, dormant-by-default, and read-only/partial.
- `scripts/check_dashboard_data.py` and dashboard integrity tests were useful for understanding current generated-artifact safeguards.
- Button/panel files under `disbot/views/**` and button-heavy cogs were needed to validate that panel layout movement requires a bot-side panel registry/layout model.

### pointed-not-needed

- Full schema file contents for every cog were not all needed because `scripts/scan_setting_specs.py` is the relevant extraction seam for the dashboard.
- Full HTML bodies of every template were not required beyond confirming route/template structure and navigation approach.

### discovered-by-hand

- `dashboard/README.md` has not caught up with `dashboard/app.py` for `/status`.
- External GitHub PR verification is blocked in this checkout because `gh` is missing and no `origin` remote is configured.
- The current control API only exposes `/control/ping` and `/control/authority`; write endpoints remain planned/gated.

## Verification

- `PYENV_VERSION=3.10.20 python scripts/export_dashboard_data.py`
- `PYENV_VERSION=3.10.20 python scripts/scan_commands.py --summary`
- `PYENV_VERSION=3.10.20 python -m pytest tests/unit/scripts/test_export_dashboard_data.py tests/unit/scripts/test_scan_commands.py`
- `PYENV_VERSION=3.10.20 python -m pytest tests/unit/dashboard/`
