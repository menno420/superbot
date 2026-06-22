# 2026-06-22 — Help-menu regrouping (simulation + implementation)

> **Status:** `complete`

Owner-directed: the Help menu had grown crowded; regroup it into a few clear,
logical sections so every feature is reachable in ≤3 button clicks. The owner
asked for a **simulation** to find the most-efficient grouping first.

## Arc

1. **Built a grouping simulation** (`tools/sim/help_menu_grouping_sim.py`, stdlib,
   read-only) that loads the live hub + subsystem registries, models the Help
   click graph exactly (index → section → child, with the 12-item dropdown
   pagination from `panels.py` that silently breaks the 3-click guarantee), and
   scores candidate groupings on reachability, cohesion, section count, and
   orphan count. It revealed the real problem: **8 subsystems were orphans**
   (`fishing`, `creature`, `welcome`, `counters`, `security`, `channel`, `ai`,
   `ux_lab`) reachable only through the paginated "All Commands" browser — `ai`
   already took 3 clicks — and the admin-side index carried **10 sections**.
2. **Confirmed the section scheme with the owner** (AskUserQuestion, sim data in
   hand): chose **Consolidated — 7 sections**.
3. **Implemented the grouping**: homed every orphan into its best-fit hub and
   nested the three child-less ops hubs (Settings · Diagnostics/Platform · Server
   Management) under one **Server & Admin** section. Result (verified by the sim's
   `live` scheme): **7 sections, 0 orphans, every feature ≤2 clicks, no
   pagination.**

## Shipped

- `tools/sim/help_menu_grouping_sim.py` — the grouping simulation (baseline vs
  live vs analytical-frontier; doubles as a regression check — re-run after any
  registry change).
- `disbot/utils/subsystem_registry.py` — `parent_hub` set on the 8 former orphans
  + the 3 nested ops hubs (fishing/creature→games; welcome/counters→community;
  security→moderation; channel/ai/ux_lab/settings/diagnostic/server_management→admin).
- `disbot/utils/hub_registry.py` — Games/Community/Moderation rosters extended;
  `admin` renamed **Server & Admin** with 6 primary children; Settings /
  Diagnostics / Server Management HubEntries removed (now `admin` children).
- `disbot/cogs/admin_cog.py` — the `_AdminPanelView` is now the Server & Admin hub:
  4 new child buttons (Server Management · Channels · AI · UX Lab), re-rowed, new
  embed copy.
- `disbot/cogs/help/route.py` — `platform` alias now → Server & Admin hub;
  `servermanagement` subsystem alias added; the (now dead) Diagnostics panel-builder
  override removed.
- `disbot/cogs/diagnostic_cog.py` — comment-only: Platform/Diagnostics reachability
  re-described (no longer a top-level hub).
- `docs/help-command-surface-map.md` — binding surface map updated to 7 hubs.
- Tests across help/admin/community/projection/registry/actionability/doc suites
  updated to pin the new IA. Full suite green (11538 passed, 2 xfailed by design),
  arch 0 errors, catalogue drift 0.

## Findings / decisions

- **fishing/creature actionability**: homing them under the Games hub subjects them
  to the Games actionability contract, which they fail (instruction-only panels).
  Carried as `xfail(strict=True)` targets — the contract's own pattern for
  "should be actionable, isn't yet" — so they auto-alarm when a Fish/Catch button
  lands. (Owner-visible: an actionable in-panel surface for fishing/creature is a
  good future game slice.)
- **welcome/counters/security** are admin-tier children of user-tier hubs; their
  `visibility_tier` keeps them operator-only in the user view (same precedent as
  `role` under Community), so no operator config leaks to normal members.
- **Platform vs Diagnostics** surfaces both survive (DiagnosticCog keeps both
  hooks); they're now reached via the Server & Admin panel's Platform / Diagnostics
  buttons rather than a top-level hub.

## ⚑ Self-initiated

None — this whole session is owner-directed (the regrouping request + the
AskUserQuestion-confirmed scheme). PR opened ready and auto-merge armed (Q-0191
owner-directed → merge on green, not held for review).

## 💡 Session idea (Q-0089)

**A `--check` mode for `help_menu_grouping_sim.py` wired into CI / the consistency
linter** — the sim already reads the live registry and computes max-clicks /
orphan-count / max-section-size. A `--check` flag that exits non-zero when *any*
feature exceeds 3 clicks, a section exceeds the 12-item dropdown page, or a new
orphan appears would turn the one-off design tool into a standing guard, so a
future subsystem added without a `parent_hub` fails fast instead of silently
falling into the paginated Advanced browser (exactly the rot this session fixed).
Genuinely worth having — the "verifiable, disposable guard" pattern (Q-0105)
applied to Help reachability. (Not built this session to keep scope tight; the sim
is structured so the flag is a small follow-up.)

## ⟲ Previous-session review (Q-0102)

Reviewed the band #1234–#1263 BTD6 / reaction-roles work (PR #1263 + neighbours).
**Did well:** the data-lifecycle hardening (auto-seed BTD6 blob data on boot,
#1255) closed a standing "owner must remember to run `seed-data`" manual step —
the kind of operator-toil removal the project should prefer. **Could have done
better / system improvement it surfaces:** that arc touched the subsystem registry
repeatedly but nobody noticed the 8 accumulated Help orphans — there was no
standing signal that "a new subsystem isn't reachable in the menu." The concrete
workflow improvement is this session's **session idea** (a `--check` mode for the
grouping sim): make Help reachability a guard, not something a human has to spot.
The orphans accreted precisely because each addition looked locally fine; a
registry-level invariant is the right altitude to catch it.

## 🔎 Doc audit (Q-0104)

- `check_docs --strict` ✓ · `check_architecture --mode strict` 0 errors ·
  `check_quality --full` ✓ · catalogue drift 0.
- `check_current_state_ledger --strict` shows #1265–#1289 not yet in
  Recently-shipped — **benign newest-merge lag** handled by the auto-triggered
  Q-0107 reconciliation pass at the #1290 boundary (Q-0124: a manual session
  pursues its own work, not the recon). This PR is correctly absent from the ledger
  until merged.
- Binding home updated (`help-command-surface-map.md`). The `building-roadmap/`
  mother-hub-map / hub-ui-standard docs still describe the pre-regrouping doctrine
  but are historical/reference (not doc-test-pinned); left for the recon pass to
  reconcile if it judges them load-bearing.

## Context delta

- **Needed but not pointed to:** the **actionability contract**
  (`tests/unit/help/test_help_actionability_contract.py`) is an invisible
  consequence of `parent_hub == "games"` — nothing in the registry or hub docs
  warns that homing a subsystem under Games imposes an "in-panel action button"
  requirement. Worth a one-line note in `hub_registry.py` or the surface map.
- **Needed but not pointed to:** the catalogue's **bidirectional roster-drift**
  rule (`parent_hub` ⇄ `primary_children` must agree both ways) lives only in
  `services/help_catalogue.py`; an editor changing one side learns about the other
  only when the test fails. The two-way contract belongs in the `hub_registry.py`
  docstring.
- **Pointed to but didn't need:** CodeGraph — this was a registry/IA change best
  navigated by `context_map.py` + targeted reads + the (thorough) hub-view Explore
  sweep; the symbol graph added nothing here.
