# 2026-06-10 — Batch 5: Adaptive P1C — Access Map + Help Preview subpanels

**Arc:** same continuation session (Batches 3/4 merged as #652/#654 along the
way); executed the consolidated plan's **Batch 5 / adaptive P1C** on a fresh
branch (`claude/batch5-adaptive-p1c` — #654 was still open on the old branch
when work started, so a new branch kept that PR clean; it merged minutes
later and the branch synced onto main).

**Shipped (PR — see branch; verify merged):**

- **`views/server_management/access_map.py`** — the first UI consumers of the
  P1A `project_access_map` projection (§16.8 item 4), per **Q-0032**: staff-hub
  subpanels only, **no new command names**.
  - **Access Map**: per-feature effective access (✅/❌/❓) for a simulated
    audience tier in the current channel; denied rows show the user-safe
    reason + deciding axis; a feature select drills into the full source
    chain (ephemeral).
  - **Help Preview**: advertised / shown-as-locked (safe reason) / hidden
    buckets for the simulated audience — §16.4's honest rendering.
  - Audience simulation = the **Q-0045 declared-tier path** (`member=None`,
    `member_tier=tier`); every rendering carries the §16.4 limit label
    (`SIMULATION_LIMIT_NOTE`).
  - **Authority-gated, not ownership-gated** (admin floor re-checked live on
    every interaction — the ModPanelView/hub pattern; `public=True` BaseView
    with an `interaction_check` override, documented).
  - **Display-only pinned by test**: the module may not import any
    `*_mutation` module or the setup dispatcher (AST import scan).
- **Hub wiring**: two new persistent buttons on the Server Management hub
  (`server_management:access_map` / `:help_preview`, row 2) that defer →
  build → edit-in-place with the back-to-hub button attached.
- **Tests**: 10 new view tests (authority re-check incl. the
  not-ownership-locked case · embed buckets/labels · tier-select rerender ·
  ephemeral source-chain drill-down · mutation-import pin) + hub custom_id
  set updated. 51 focused green; full CI mirror green; arch strict 0 errors.
- **Live smoke**: booted Galaxy Bot — clean boot, 0 errors, hub registered
  with the new custom_ids.

## Decisions made alone (ratify if they matter)

1. **Default simulated audience = tier `user`** (the baseline a normal member
   experiences — matches `help_advertises_locked`'s baseline concept); a
   select switches to trusted/staff/moderator/administrator (§6.3's set).
2. **Both panels simulate (member=None) rather than projecting the clicking
   admin's real member** — the panels answer "what do *members* see here",
   and the declared-tier path keeps one cache entry per tier (Q-0045 note).
3. **Source-chain drill-down is ephemeral and shows internal axis details** —
   acceptable because the panel is admin-gated end-to-end; sub-admin
   surfaces only ever see `LockedReason.safe_text` (unchanged).
4. **Subpanels are transient views** (BaseView, 180s), not PersistentViews —
   they're drill-downs from the persistent hub; restoration would add
   custom_id surface for no operator value.

## Flagged for maintainer / known limits

- The feature drill-down select caps at Discord's 25 options (the map embed
  shows every feature; only the select truncates). Fine at 29 subsystems
  minus allows… borderline — if the inventory grows, paginate the select
  like the Settings hub did (#640 pattern).
- Help Preview projects help-axis state from the P1A projection — it is NOT
  yet the literal Help renderer output. That convergence is exactly Batch 6
  (the Help projection seam consuming this lane), per the plan.
- The §16.4 label is a constant; if the wording should match some future
  user-facing copy table (Q-0036 lane), update `SIMULATION_LIMIT_NOTE`.

## Context delta

- **Needed but not pointed to:** nothing major — §16.8 item 4 named
  `project_access_map` as the P1C surface and it was exactly right.
- **Discovered by hand:** the hub's `_attach_back_to_hub` + routed-manager
  edit-in-place pattern (the natural template for subpanel navigation); the
  back button must be *carried* across tier re-renders (a new view replaces
  the old one — `_copy_back_button`).
- **One change that would have helped:** none — this lane's docs trail
  (Q-0032 + Q-0045 + §16.4/§16.8) was the most complete of the five batches.
