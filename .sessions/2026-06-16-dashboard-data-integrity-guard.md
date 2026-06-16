# 2026-06-16 — dashboard.json integrity guard

> **Status:** `in-progress` — born-red per Q-0133; flipped to `complete` as the deliberate
> final step. Tooling + tests only (no `disbot/` runtime, no dashboard templates).

## What I'm about to do

The owner is shipping the control-panel **write path** (mutation endpoints) and the **website OAuth
+ editors** in parallel sessions, and asked me to continue with **something non-conflicting**. So I
pivoted *off* the control-API read endpoints I'd started scoping (they'd collide with the
mutation-endpoints session in `control_api.py`) onto a slice that touches neither `control_api.py`
nor the website OAuth/editor pages.

Build **`scripts/check_dashboard_data.py`** — a stdlib integrity guard for the dashboard's exported
`dashboard.json`. The dashboard is now the bot's main website, extended by **many parallel sessions**;
an export-integrity validator catches the drift classes that silently degrade pages (I hit one this
very session — acronym cogs whose `subsystem` didn't resolve to the registry, so they rendered with
a generic icon + no routing key). Checks:

- **cog→subsystem resolution** — every real (`is_cog`) cog's `subsystem` resolves to a registry
  subsystem, minus a curated allow-list of legitimately-unregistered cogs (BTD6 sub-cogs · Hermes ·
  Paragon · Setup · RPS) and modules/mixins. A *new* unregistered cog or a broken join fails.
- **count integrity** — `meta.counts.*` match the actual array lengths (the #973 count-drift class).
- **required fields** — every command has a name + valid type; every cog has a file; etc.

Touches only `scripts/` + `tests/` — guaranteed non-conflicting with both owner sessions and the
other dashboard sessions touching templates.

## Status checklist

- [ ] `scripts/check_dashboard_data.py` (validate + CLI, Q-0105 header)
- [ ] `tests/unit/scripts/test_check_dashboard_data.py` (synthetic drift + live-export guard)
- [ ] my Q-0089 idea file → shipped; README updated
- [ ] `check_quality --check-only` + the new tests green
- [ ] session enders + flip card `complete`
