# 2026-06-19 — Consistency linter: extend rules 3+4 to the cog layer

> **Status:** `in-progress`

Routine dispatch run (empty fire → live ▶ Next-action follow-up). Executing the routed
follow-up named in `docs/current-state.md` ▶ Next action: **extend the consistency
linter's `select_option_truncation` (rule 4) and `panel_base_class` (rule 3) rules to
scan `disbot/cogs/`** — BUG-0017 (the Cog Manager `options[:25]` silent drop) existed
precisely because those rules are `views/`-scoped, so the cog layer is a real blind spot
for the exact `#1040` truncation class the linter exists to catch.

## Plan

- Make rule scope **per-rule** (a `Rule.roots` attribute) instead of a hard-coded
  `views/` filter, so a rule can opt into additional roots without copy-pasting the
  scan loop.
- Set `roots=("views/", "cogs/")` on rule 3 (`panel_base_class`) + rule 4
  (`select_option_truncation`); rules 1+2 stay `views/`-only (rule 1 is warn-only and
  blocked on the AI-nav redesign; rule 2's HubView nav panels live in `views/`).
- Triage every NEW cog-layer finding the extension surfaces: real bug → fix at root;
  legitimate top-N / fixed-catalog → allowlist with a per-entry reason. Both rules are
  GRADUATED (`severity="error"`, wired into `code-quality.yml`), so they must land at
  **0 findings** to keep CI green.

## Shipped

_(in progress)_
