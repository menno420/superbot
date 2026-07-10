# 2026-07-10 — dashboard.json pinned-feed contract, first slice (overnight shift, session D)

> **Status:** `in-progress`
> **Branch:** `claude/shift-d-dashboard-contract` · **PR:** TBD

**Intent:** shift-plan item **K3** — apply the #1884 console pinned-feed-contract
pattern to `dashboard/data/dashboard.json` (the ~12-page websites surface with no
contract), scoped to ONE family slice: `meta` + `bugs`. New versioned
`dashboard/data/dashboard_data_contract.json`, producer `schema_version` stamp +
parity constants in `scripts/export_dashboard_data.py`, fail-closed
`check_dashboard_contract` + CLI flag in `scripts/check_dashboard_data.py`, tests in
`tests/unit/scripts/`. Ride-alongs: **Q2** — justifying comments on the 6
undocumented `baseview_inheritance` direct-`discord.ui.View` warnings (comment-only,
zero runtime delta); **Q1** — `trim_recently_shipped.py --apply` docs pass.
Idea: `docs/ideas/pinned-feed-contract-for-dashboard-json-2026-07-09.md`.
