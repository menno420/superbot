# 2026-06-23 — Phase-0 completion: hub-child primitive + settings-orphan guard + fleet plan

> **Status:** `complete` — owner-directed: finish the Phase-0 rails so the ultracode consolidation
> fleet can run safely. #1370 shipped the per-command reachability guard (the key machine reviewer) +
> the general-cog fix; this completes the remaining rails. PR this session, auto-merge armed on green
> (Q-0127). Owner-directed → merge immediately (Q-0191).

> **Run type:** `manual · owner-directed`

## What I'm about to do

1. **Shared hub-child-rendering primitive** — extract the `discover_*_children` + child-button pattern
   (today copied in `views/games/hub.py`, `views/community/hub.py`, `cogs/utility_cog.py`) into one
   helper, and fix the 2 known per-command reachability gaps **through it**: `!btd6strat` (BTD6 hub
   doesn't surface the Strategy child) and `!temproles` (`role_grants` not homed/surfaced). The
   per-command guard (#1370, CI-enforced ratchet) is what proves only these 2 remain.
2. **Settings-orphan ratchet guard** — promote `actionable_settings_groups()`'s
   `settings_without_panel`/`panels_without_settings` diagnostics into a warn-first ratchet
   (test + allowlist), mirroring `check_command_reachability`, so the fleet's "settings reachable"
   rubric item is machine-checked.
3. **`consolidation-fleet-plan-2026-06-23.md`** — the artifact ultracode reads: 12-unit disjoint
   roster + the 23-file held set + Phase-0 status + per-agent template + the born-red→coordinator-merge
   protocol.

## What shipped vs. what I specced (honest split)

**Shipped + verified:**
- **Shared hub-child discovery primitive** — `disbot/views/hub_children.py` `discover_hub_children(hub_key)`;
  the games / community / utility hubs now all **delegate** to it (one source, 3 consumers). Pure,
  registry-only. New `tests/unit/views/test_hub_children.py` (incl. delegation-equivalence). Full view
  suite green (1747 passed); mypy clean; 0 arch errors; lint clean.
- **`consolidation-fleet-plan-2026-06-23.md`** — the ultracode coordinator's brief: Phase model, the
  Phase-0 rails status, the **held set** (the shared files no worker may touch), the **file-disjoint
  unit roster** (U1–U11), the per-agent template, and the born-red→coordinator-merge protocol. Homed in
  `planning/README.md`.

**Specced, not built (with reason):**
- **Settings-orphan guard → Phase 0.5.** I verified the live `customization_catalogue` discovers panels
  by walking the live bot, so `build_catalogue(None)` returns **0/0 offline** — it's blind in CI. A
  CI-safe guard needs a static AST panel-discovery reimplementation. Rather than ship a no-op/inaccurate
  guard (the exact rushed work the audit prevents), I specced the **turn-key approach** in the plan
  (reuse `check_command_reachability._subsystem_discoverable` + `all_schemas()`), to build before the
  settings fleet wave (it does NOT gate the AI-panel/roles waves).
- **The 2 known gaps** (`!btd6strat`, `!temproles`) — routed as fleet units U4/U2: they're bespoke
  per-cog judgment work (BTD6's hand-built panel needs a Strategy sub-view; `role_grants` needs a homing
  decision), not primitive applications. The per-command guard (#1370) keeps them visible + CI-ratcheted.

> **⚑ Self-initiated:** none of bot-feature kind. Owner-directed rails/consolidation; the `discover_*`
> delegation is a contained refactor (collaboration-model act-on-contained).

## 💡 Session idea (Q-0089)

**A `check_hub_children_rendered` invariant.** The discovery half is now shared, but a hub panel can still
*forget to render* a discovered child (the original general-cog bug — Utility had the registry entry but
no button). The per-command guard catches it indirectly (the child's commands go unreachable). A direct
invariant — "for each hub, the rendered panel's buttons cover `discover_hub_children(hub_key)`" — would
catch it at the panel layer too. Needs loading the hub views + reading their child buttons; pairs with the
`HubChildButton` consolidation (a shared button makes the coverage statically checkable). → relates
`views/hub_children.py` · `check_command_reachability.py`.

## ⟲ Previous-session review (Q-0102)

#1370 (Session 1) did the highest-value thing first — the per-command reachability guard — and that
turned out to be the load-bearing rail: it makes the fleet safe even *without* the shared primitive,
because an orphaned command fails CI. Its one miss was adding a **third** `discover_*_children` copy
(utility) instead of extracting the primitive — understandable under time, and exactly what this session
consolidated. **System improvement:** the born-red gate + per-command ratchet are a strong template for
"new guard = a warn-first ratchet test in `tests/unit/invariants/` + an allowlist yaml"; worth codifying
that 3-file shape (script + ratchet test + exceptions yml) as a `/new-guard` skill so the settings guard
(and future ones) are fill-in-the-blanks.

## 📋 Doc audit (Q-0104)

Findings in durable homes: the primitive is code+test; the fleet plan is committed + homed in
`planning/README.md`; the settings-guard spec + 2-gap routing live in the plan. `check_docs --strict` ✓,
`check_quality --check-only` ✓, arch 0 errors, mypy clean. No new owner decision (executes prior ones) →
no router entry owed. Reconciliation marker untouched (no merged-PR ledger edit). Repo is staged: Phase-0
rails are green for the AI-panel + roles fleet waves; settings wave waits on the Phase-0.5 guard.
