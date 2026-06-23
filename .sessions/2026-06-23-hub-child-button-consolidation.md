# 2026-06-23 — HubChildButton consolidation (discoverability fleet, first consolidation)

> **Status:** `complete` — the fleet plan's flagged **"first consolidation"** shipped (PR #1373). Full CI
> mirror green (12119 passed); arch strict 0. Continuation of the discoverability audit (#1370 foundation
> · #1371 rails · #1372 U4). Self-merge on green (no active fleet coordinator).

> **Run type:** `manual · continuation`

## What I did

After #1371 shared the *discovery* half (`discover_hub_children`), the *button* half was still 3 copies.
Extracted the shared **`HubChildButton`** into `views/hub_children.py` and migrated the two byte-identical
copies onto it:

- **`HubChildButton`** holds the common open-child-in-place logic (click-time governance recheck →
  `_cog_for_subsystem` → `build_help_menu_view` → hub Back-nav + Back-to-Help grandparent threading →
  edit in place), parametrized by `hub_key` (custom_id), a per-hub `back_attacher`, and an optional
  `fallback_builder`.
- **`_CommunityChildButton` / `_UtilityChildButton`** are now thin subclasses that bind their `hub_key` +
  back-attacher — the inline duplication (~55 lines each) is gone, and the public names + tests are
  unchanged (so all 74 hub tests + the community/utility suites pass untouched).
- **Behaviour-preserving:** community + utility pass no `fallback_builder`, keeping their ephemeral-error
  path; the `f"{hub_key}:open:{subsystem}"` custom_ids are unchanged (persistence-safe). The
  refactor also shrank `utility_cog.py` back under the cog-size warn-tier.
- **Games-ready, not migrated:** the `fallback_builder` param matches games' richer in-place fallback, so
  games adopts the shared button as a **drop-in U3 follow-on** (subclass + drop `handle_select`); its
  dropdown-legacy guards stay for now. Added 5 direct `HubChildButton` tests incl. the `fallback_builder`
  branch neither hub exercises.

Updated the fleet plan: the "first consolidation" is marked **done**, with games' drop-in migration the
only remainder; the U6/U11 "migrate child-buttons" tasks are struck (done by this PR).

**Acceptance met:** community + utility nav behaviour identical (tests pin it); full CI mirror + arch
strict green. Contained to `hub_children.py` (held-set — safe, no active fleet) + the 2 hubs + tests.

> **⚑ Self-initiated:** picking up the "first consolidation" (the fleet plan's flagged good-early-unit)
> was the next startable item; the fleet-plan status updates are drift-on-sight (Q-0166). All reversible,
> test-covered, behaviour-preserving. No new owner decision.

## 💡 Session idea (Q-0089)

**A consistency-linter rule that flags a hand-rolled hub child-button.** This consolidation removed 2 of
3 copies, but nothing *stops* a future hub (or a careless edit) from re-introducing a 4th hand-built
`discord.ui.Button` subclass that forwards to `build_help_menu_view` instead of using `HubChildButton` —
the same "drift breeds a 4th copy" risk the discovery-half had before #1371. A `check_consistency.py`
rule — *a `HubView`/hub panel that constructs child-forwarding buttons must use `HubChildButton`* (AST:
flag a `discord.ui.Button` subclass whose callback calls `build_help_menu_view`, outside
`hub_children.py`) — would make the consolidation **un-regressable**, exactly as the per-command
reachability guard (#1370) did for findability. Cheap, high-leverage, and it closes the loop on this
whole "shared hub primitive" thread. Captured for grooming → `docs/ideas/`.

## ⟲ Previous-session review (Q-0102)

The previous session (my own U4, #1372 — surfacing `!btd6strat`) was clean and complete: it fixed the
gap with a real panel button, source-cited the allowlist, shrank the guard baseline, *and* caught +
corrected the fleet plan's Phase-0.5 `all_schemas()`-is-empty error. **What it could have done better:**
it ended at "one gap fixed" when the fleet plan had a clearly-flagged, contained, ready quick-win sitting
right there — the "first consolidation" (this session's work) — that it could have bundled or teed up
explicitly. **System improvement it surfaces:** the fleet plan's "first consolidation" callout was
discoverable but easy to skip past; a session-ender habit of *"before closing, scan the active plan's
flagged quick-wins / good-early-units and tee up the next one"* would shorten the gap between "a
consolidation is specced" and "it's done." This session is that habit applied — and it found the win in
one read of the plan.

## 📋 Doc audit (Q-0104)

Anything not in a durable home? **No.** The consolidation is self-documenting (the `hub_children.py`
module docstring now describes both shared halves + the subclass pattern; the 5 new tests pin the shared
logic incl. the fallback branch). The fleet plan reflects the new state (first consolidation done; games
drop-in remaining; U6/U11 tasks struck). `check_quality --full` ✓, arch strict 0, `check_docs --strict`
✓. No new owner decision → no router entry owed. Reconciliation marker untouched (next pass at #1380
records #1370–#1373).

## 📤 Run report

- **Run type:** `manual · continuation` (the fleet plan's "first consolidation").
- **Slices shipped this run:** 1 PR (#1373) — the shared `HubChildButton` + community/utility migration +
  5 tests + the fleet-plan status update.
- **⚑ Self-initiated:** the consolidation pickup + fleet-plan drift fixes. No invented features;
  behaviour-preserving refactor.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none — pure refactor, no migration/data; the merge auto-deploys. No live
  behaviour change (custom_ids preserved; existing anchors keep routing).
- **Bug-book:** no entries opened/closed.
