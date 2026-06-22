# 2026-06-22 — BUG-0023 root fix: scanner discovers `app_commands.Group` attribute slash commands

> **Status:** `in-progress` — Dispatch routine (no work order). Empty-fire run; bugs-first picked the
> top offline-fixable bug-book item: **BUG-0023 slash under-coverage**. Self-initiated (Q-0172).

> **Run type:** `routine · dispatch`

## What I'm about to do

BUG-0023's one real gap — *"static scan finds **25** slash, the live tree has **71** → the website
under-documents slash commands"* — was hypothesised in the bug book as *"dynamically-registered app
commands / context menus the AST cannot see."* **That hypothesis is wrong.** Investigated this run:

- 0 context menus, 0 `tree.add_command`, 0 hybrids in the codebase.
- The gap is **`app_commands.Group` declared as a class *attribute*** (`ai_app_group =
  app_commands.Group(name="ai", …)`) with subcommands decorated `@ai_app_group.command(…)`, in 6 cogs
  (ai · btd6 · btd6_events · btd6_ops · btd6_reference · btd6_strategy).
- `scan_commands._find_groups` only detects groups declared as **decorated methods**
  (`@app_commands.group`), so it misses these groups **and every subcommand under them**.
- Exact reconciliation: **25 standalone + 40 subcommands + 6 groups = 71** = the live tree count. All
  46 missing commands are **statically discoverable** — no runtime-aware counting needed.

This run: teach `scan_commands.py` to detect attribute-assigned `app_commands.Group` (and
`HybridGroup`) groups so their subcommands are scanned and the groups counted, regenerate the
dashboard/site data, and close BUG-0023's slash under-coverage at the root with a regression test.

## Files (planned)

- `scripts/scan_commands.py` — detect `X = app_commands.Group(...)` class-attr groups → register the
  group + scan its `@X.command` subcommands (inherit `slash`/`both`); emit the synthesized group record.
- `tests/unit/scripts/test_scan_commands.py` — a sample cog with an attribute-assigned slash group +
  subcommands; assert the group and its subcommands are scanned (fails against the pre-fix behaviour).
- regenerate `dashboard/data/dashboard.json` · `botsite/data/site.json` · `botsite/site/data.js`.
- `docs/health/bug-book.md` — mark BUG-0023 slash under-coverage FIXED (root) with the reconciliation.

## What shipped

_(filled at completion)_
