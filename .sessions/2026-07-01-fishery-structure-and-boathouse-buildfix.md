# 2026-07-01 — Fishery (4th fishing structure) + Boathouse build-crash root fix

> **Status:** `complete` — ready to merge (Q-0133). Run type: routine · dispatch.
> Full CI mirror green locally (**13724 passed**, 48 skipped; ruff/black/isort/mypy clean; arch 0 new).
> The only red check was the born-red session gate (now flipped). PR #1626.

**Branch:** `claude/funny-franklin-lkqjh9`.

## What shipped

Scheduled dispatch fire, **no work order** → advanced the S1 ▶-next offline slice (the "fourth fishing
structure") + a bugs-first root fix found during orientation.

### 1. BUG-0031 (bugs-first, root) — Boathouse build crashed with `KeyError`
`services.mining_workflow.build_structure` resolved the economy-audit reason via
`_STRUCTURE_BUILD_REASON[structure]` — a hand-maintained map that **never got a `boathouse` entry**
when #1605 shipped the Boathouse, so `!boathouse` **Build** raised `KeyError: 'boathouse'` in prod (no
test exercised the build path → CI stayed green). Reproduced it directly before fixing. Root fix kills
the drift class: the map is deleted and the reason is derived generically via
`market.structure_build_reason(structure)` → `mining:{structure}_build` (exactly what every named
constant already spelled). Stays-fixed guard: `test_every_registered_structure_resolves_a_build_reason`
loops `structures.STRUCTURES` and fails against the pre-fix direct-index map. Bug-book BUG-0031 (FIXED
root). Also added the missing Boathouse + new Fishery build-confirmation reward lines for parity.

### 2. Feature — the Fishery (4th coral structure, yield/abundance lever)
The three prior coral structures cover quality (Tide Pool → rarer fish), throughput (Dock → faster
bites), endurance (Boathouse → energy regen). The **Fishery** is the fresh **yield** axis — a built
fishery raises the lucky **double-catch** chance (`+0.05/level` over the base `0.10`). Computed once in
`begin_cast` from the existing structures read and threaded onto `Cast.double_catch_chance` so
`commit_catch` stays DB-free; byte-identical when unbuilt. `roll_bonus_catch` gained an optional
`chance` override (clamped `[0,1]`, default-preserving). Coral + wood sink on the generic
`mining_structures` table (**no migration**), audited `build_structure` seam, `views/fishing/fishery.py`
panel + a 🐟 button in the 🏗 Structures sub-hub + `!fishery` (aliases `hatchery`/`fishfarm`, collision-
checked). Sim-pinned: `docs/planning/fishing-fishery-numbers-2026-07-01.md`.

**Tests:** +8 structures-math, +1 workflow double-catch, +3 hub-view (button/embed/back) = green.
Files: `structures.py`, `market.py`, `mining_workflow.py`, `fishing_workflow.py`, `rewards.py`,
`views/fishing/{fishery.py,structures_hub.py,__init__.py}`, `cogs/fishing_cog.py`, 3 test files,
regenerated dashboard/site artifacts, S1-bot ledger, bug-book.

## Handoff / continuation (next dispatch)

The fishing-structures arc now has four axes (quality/throughput/endurance/yield). ▶ **Next offline
successors** (S1-bot ▶ Next, all self-mergeable): a *fifth* structure would need yet another fresh
lever — the obvious one is a **coin-yield "Fish Market"** (a sell-value bonus for fish), but that
crosses into the shared mining sell path (`mining_workflow.sell`/`sell_all` distinguish fish from ore)
so it's a bigger, less-contained change than the four in-`begin_cast` knobs — worth its own scoping.
Otherwise the fishing **open-world expansion** (`planning/fishing-open-world-expansion-plan-2026-06-18.md`
Phase 2). No blockers; CodeGraph + tooling were all available this run.

## Session enders

**💡 Session idea (Q-0089):** a **structure-registry completeness checker** — assert every
`structures.STRUCTURES` entry has (a) a resolvable build reason [now generic], (b) a `!command` +
panel button reaching it, and (c) a test that drives `build_structure` for it. BUG-0031 was exactly
this class: a structure *registered* (ladder/names/panel) but with an un-exercised code path that
crashed. My regression test closes the reason sub-case; a registry-completeness guard would catch the
whole class (a structure shipped without a working build/command/panel) at CI instead of in prod.
Genuinely worth having — I believe in it; capturing as a follow-up, not building it this run to keep
the PR cohesive.

**⟲ Previous-session review (Q-0102):** the prior run (#1618, server-log subject avatars) was clean,
additive, and well-scoped — a good "one improvement" response to the owner's Dyno comparison. What it
*missed / could improve:* it explicitly deferred the moderation/audit embeds (`format_log_embed`/
`format_audit_embed`) because they "only carry ids, not objects" — but resolving the member from the
guild (`guild.get_member(id)`) is genuinely trivial, so those two surfaces still lack the avatar the
rest of the log now has; a follow-up should close that gap so the "face per entry" is truly universal.
**System improvement it surfaces:** the born-red gate works well, but a *cohesion* signal is missing —
nothing flags when a PR touches N unrelated subsystems; a lightweight "diff spans >1 sector" advisory
would nudge sessions to split, complementing the merge gate.

**📋 Doc audit (Q-0104):** ledger check clean (only benign #1624/#1625 newest-merge lag, next recon
records them); new numbers doc linked from S1-bot (orphan check green); bug-book BUG-0031 added;
dashboard/site artifacts regenerated (freshness guard green); no owner decisions to route.

## 📤 Run report

- **Run type:** routine · dispatch
- **PR:** #1626 (Fishery structure + BUG-0031 boathouse build-crash root fix)
- **Shipped:** 1 feature (Fishery, 4th fishing structure) + 1 root bug fix (BUG-0031) + tests + docs
- **⚑ Self-initiated:** the Fishery feature (no work order — the standing S1 ▶-next offline slice) and
  the BUG-0031 root fix (found during orientation, bugs-first). Both grounded in the live plan /
  bug-book, not invented. Owner can review/revert via PR #1626.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (merge auto-deploys; no data step)
