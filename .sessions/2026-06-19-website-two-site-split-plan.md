# 2026-06-19 — Website two-site split: the implementation plan (Q-0178)

> **Status:** `in-progress`

## Arc

Execute the planning session the previous PR (#1099) specified: read the
`website-two-site-split-planning-brief-2026-06-19.md` brief + router Q-0178, and produce the **full
implementation plan + file-disjoint ultracode decomposition** for splitting the single `dashboard/`
service into a public **bot site** and a repurposed **dev/repo site**. No runtime code — planning only.

## What I'm about to do

- Ground the plan in the *actual* current dashboard (routes in `dashboard/app.py`, the decoupled data
  producer `scripts/export_dashboard_data.py`, the private bot `control_api.py`, the Railway deploy shape).
- Write `docs/planning/website-two-site-split-plan-2026-06-19.md` covering all 7 required deliverables.
- Forward-link it from the brief + current-state ▶ Next action; claim + close active-work.
