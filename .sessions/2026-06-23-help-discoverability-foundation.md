# 2026-06-23 — Discoverability audit Session 1: help-findability foundation

> **Status:** `complete` — Session 1 of the owner-directed consolidation/discoverability audit
> ([brief](../docs/planning/consolidation-discoverability-audit-brief-2026-06-23.md) Appendix A)
> shipped (PR #1370). Full CI mirror green (12108 passed); arch strict 0. Owner-directed (the
> previous session staged this as the explicit next task) → merge on green (Q-0191).

> **Run type:** `manual · owner-directed` (continuing the work the previous session prepared)

## What I did

The foundation session of the per-cog discoverability audit (not a feature pass; **not** the AI/roles
panel refactors — those are Sessions 2/3). All four steps of the kickoff prompt:

1. **Root-caused the general-cog "unfindable" report — statically, no live guild.** Traced `!help` →
   `HelpCategoryView` → Utility hub → General. **Cause (b), structural:** the Utility hub panel
   (`_UtilityPanelView` in `cogs/utility_cog.py`) is a *hybrid* surface (its own actions + parent hub of
   `general`/`four_twenty`) but rendered **only its own action buttons and never surfaced its child
   subsystems** — unlike the Games (`views/games/hub.py`) / Community (`views/community/hub.py`) hubs,
   which discover children from `SUBSYSTEMS` (`parent_hub == …`) and render forwarding buttons. So the
   click-path dead-ended (`!help` → Utility → 6 buttons, **no General**) and a new user could never reach
   `!joke`/`!fact`. Cause (c) ruled out — `general` is `visibility_tier: user` / `mode: normal`, never
   default-hidden.

2. **Fixed the deterministic part** — `_UtilityPanelView` now renders a forwarding button per child
   (`discover_utility_children()` + `_UtilityChildButton`, row 3, click-time governance recheck +
   Back-to-Utility, mirroring the Community hub) **and lists the children in its embed**. Contained to
   `utility_cog.py`; guarded by `tests/unit/cogs/test_utility_hub_children.py` (8 tests).

3. **Built the per-command reachability guard** (`scripts/check_command_reachability.py` +
   `tests/unit/invariants/test_command_reachability.py`, **warn-first ratchet**, allowlist
   `architecture_rules/command_reachability_exceptions.yml`). Static, reuses the live cog→subsystem
   resolution (`cog_name_to_subsystem` + entry_points, the `_cog_for_subsystem` rule). Classifies every
   prefix command reachable / exempt / gap. The invariant ratchets against a 2-entry baseline so *new*
   unreachable member commands fail while the recorded gaps are tolerated.

4. **Ran it across all cogs + recorded the per-cog gap list**
   ([`docs/audits/command-reachability-gaps-2026-06-23.md`](../docs/audits/command-reachability-gaps-2026-06-23.md)):
   **214 prefix commands → 75 reachable · 137 exempt · 2 genuine gaps.** The 8 initially-flagged gaps were
   verified against source (Q-0120 — a checker that fights the evidence is the checker's bug): **6 were
   already reachable via a hub-panel button / panel text** (btd6events→"Live Events", btd6ref→"Towers/
   Heroes/CT", paragon→"Paragon", cbattle/cbattletop→creature panel text) → allowlisted with citations,
   **incl. `!cbrecord` which was a one-line omission I fixed** (added next to its two siblings in
   `creature_cog.build_help_menu_view`, then allowlisted like them). The **2 left** are genuine
   (`!btd6strat` — no Strategy button in `BTD6PanelView`; `!temproles` — not in any roles panel), each a
   tiny per-cog follow-on left for the per-cog sessions.

**Acceptance met:** root cause documented + fixed; guard exists (warn-first) + emits the gap list;
`check_quality.py --full` + `check_architecture.py --mode strict` green. Also GC'd the stale merged
claim `claude__audit-kickoff-prompt.md` (its branch merged via #1369).

## Findings / decisions

- **No new runtime bugs** beyond the discoverability gap itself. The `!cbrecord` help-text omission was a
  real (tiny) member-facing gap, fixed on sight.
- **The guard is static and can't see hand-wired panel buttons** — that's the documented limitation; the
  5 reachable-via-panel commands were verified by reading the panels and allowlisted with source
  citations, so the gap list reflects only *genuinely* undiscoverable commands (credible, low-noise).
- **`utility_cog.py` is now 688 LOC** (cog-size warn-tier 500–800; well under the 800 hard ceiling). The
  child-button machinery duplicates Games/Community — see the 💡 idea for the convergence that would also
  shrink it.
- **Doc-drift corrected:** the brief estimated "70 subsystems / 55 cogs"; the registry `SUBSYSTEMS` is
  **41** (noted in the audit doc). `help-command-surface-map.md`'s utility row now reflects the hybrid
  child-surfacing; it links the new guard + gap ledger (kept reachable).

> **⚑ Self-initiated:** the `!cbrecord` help-text fix + the 6 source-verified allowlist entries were not
> named in the kickoff prompt but fall inside step 4 ("record the gap list, note clean vs follow-on") —
> verifying each flagged command against source is what makes the list honest (Q-0120). All reversible,
> test-covered. No new owner decision (executed a prepared, owner-directed plan).

## 💡 Session idea (Q-0089)

**Generalize the hub-child-surfacing guard to *every* hub.** The reported bug (Utility hub orphaned its
`general` child) is a **view-rendering** gap the registry-level guards can't catch — `general` was
correctly homed; the *panel* just didn't render it. I guarded the Utility hub specifically
(`test_utility_hub_children.py`), but the same class can recur in any hub with a hand-built panel. A
single invariant — *construct each hub's help panel view and assert it surfaces every
`parent_hub`-declared child* (Games/Community/Utility already pass; Admin/Economy/Moderation/BTD6 to
verify) — would make the whole bug class un-regressable, the structural sibling of the per-command guard.
Pairs naturally with extracting a shared `HubChildButton` primitive (the `_UtilityChildButton` /
`_CommunityChildButton` / Games-forwarding triplicate — brief §5 convergence), which would also shrink
`utility_cog.py` back under the warn-tier. Captured here; route to `docs/ideas/` for grooming.

## ⟲ Previous-session review (Q-0102)

The previous session (the consolidation-findings-brief / kickoff-prompt staging, #1366/#1369) did the
**hard part exceptionally well**: it code-verified the shipped-vs-planned status drift (karma/starboard/
reaction-roles), wrote a genuinely *paste-ready* kickoff prompt with the repro already narrowed to
cause (b)/(c), and pre-ruled-out cause (a) by checking the buttons exist — that narrowing is exactly why
this session could root-cause statically in one pass. **What it missed / could improve:** its scale
figures were prose estimates ("70 subsystems", "55 cogs", a `GeneralMenuView` class name that's actually
`_GeneralPanelView`) — the registry is 41 subsystems, and a reader chasing "70" would waste time. **System
improvement it surfaces:** a "code-verified" brief should pin its *counts* to a runnable command, not
prose — which is exactly what this session's guard does (it *emits* the 214/75/137/2 numbers, so they
can't drift). Generalizing that discipline (counts in audit docs cite the command that produces them) is a
cheap durable win; the new guard is the first instance of it for the help surface.

## 📋 Doc audit (Q-0104)

Anything from this session not yet in a durable home? **No.** The root cause + fix + guard are in the
brief (§3.2/§8 + the Session-1 banner), the per-cog gap list is in
`docs/audits/command-reachability-gaps-2026-06-23.md` (reachable from `help-command-surface-map.md`, a
binding doc), the S1 sector file's ▶ queue reflects Session 1 shipped + Sessions 2/3 next, and this log
carries the findings + enders. `check_docs --strict` ✓, `check_quality --full` ✓, arch strict 0. No new
owner decision was made (this executed a prepared owner-directed plan), so no router entry is owed. The
reconciliation marker is untouched (no merged-PR ledger change — that's next session's reconcile).

## 📤 Run report

- **Run type:** `manual · owner-directed` (Session 1 of the prepared discoverability audit).
- **Slices shipped this run:** 1 PR (#1370) — the help-findability foundation: Utility hub child-surfacing
  fix + the per-command reachability guard + the gap ledger + the `!cbrecord` one-line fix.
- **⚑ Self-initiated:** the `!cbrecord` fix + 6 source-verified allowlist entries (inside step 4's "record
  + verify" mandate; reversible, test-covered). No invented features.
- **⚑ Owner-decisions:** none (executed a prepared plan; no router Q owed).
- **⚑ Owner-manual-steps:** none — no migration, no data step; the merge auto-deploys. An owner screenshot
  of `!help` → Utility is *welcome as confirmation* but not needed (root cause found statically).
- **Bug-book:** no entries opened/closed (the discoverability gap was fixed in-session, not tracked).
