# 2026-06-23 — Discoverability audit Session 1: help-findability foundation

> **Status:** `in-progress` — executing Session 1 of the owner-directed consolidation/discoverability
> audit ([brief](../docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md) Appendix A).
> Born-red card; the merge gate holds until I flip this to `complete` as the deliberate final step.
> Owner-directed (the previous session staged this as the explicit next task) → merge on green (Q-0191).

> **Run type:** `manual · owner-directed` (continuing the work the previous session prepared)

## What I'm about to do

The foundation session of the per-cog discoverability audit. **Not** a feature pass; **not** the
AI/roles panel refactors (those are Sessions 2/3 — scope discipline). Four steps, in order:

1. **Reproduce the general-cog "unfindable" report (static — no live guild).** Trace `!help` →
   `HelpCategoryView` → Utility hub → General; determine why a new user can't find `!joke`/`!fact`/etc.
   — cause (b) path-to-menu vs (c) a routing/governance default. Root cause with file:line evidence;
   flag the one thing needing the owner's live screenshot.
2. **Fix the deterministic part** of that root cause through the existing `help_projection` seam — one
   contained change, no new parallel system.
3. **Build the per-command reachability guard** (rubric item 2): every registered user-facing command
   resolves to a help-tree listing *or* a buttonized panel action; `internal`/owner-tier exempt via
   allowlist; **warn-first**. Modeled on `check_consistency.py` house style + `test_discoverability.py`.
4. **Run it across all cogs**, record the per-cog gap list, note clean vs. needs-follow-on.

**Acceptance:** general-cog root cause documented + deterministic part fixed; the per-command guard
exists (warn-first) and emits the full gap list; `check_quality.py --full` + `check_architecture.py
--mode strict` green.

Also GC'd the stale merged claim `claude__audit-kickoff-prompt.md` (its branch already merged via #1369).
