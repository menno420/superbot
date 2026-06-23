# 2026-06-23 — HubChildButton consolidation (discoverability fleet, first consolidation)

> **Status:** `in-progress` — continuing the discoverability audit after the foundation (#1370), the
> Phase-0 rails (#1371 — shared `discover_hub_children`), and U4 (#1372 — `!btd6strat`). This is the
> fleet plan's flagged **"first consolidation"**: the *button* half of the hub child-surfacing seam
> (#1371 did the *discovery* half). Born-red card; flip to `complete` last → self-merge on green (no
> active fleet coordinator, 0 open PRs).

> **Run type:** `manual · continuation`

## What I'm about to do

After #1371 extracted `views/hub_children.py::discover_hub_children` (one discovery seam, 3 consumers),
the **button half** is still duplicated: `_CommunityChildButton` (`views/community/hub.py`),
`_UtilityChildButton` (`cogs/utility_cog.py`), and the games child button (`views/games/hub.py` via
`handle_select`). The community + utility copies are byte-identical (I modelled utility on community in
#1370).

Extract a shared **`HubChildButton`** into `views/hub_children.py`:
- `custom_id = f"{hub_key}:open:{subsystem}"` (preserved for persistence);
- the common callback: click-time governance recheck → `_cog_for_subsystem` → `build_help_menu_view` →
  parametrized `back_attacher(sub_view, author, grandparent=...)` + grandparent threading → edit in place;
- an optional `fallback_builder` so a missing cog/hook/exception edits a graceful in-place embed
  (games' behaviour) instead of an ephemeral error (community/utility's) — i.e. **games-ready** without
  touching games now.

Migrate **community + utility** onto it (behaviour-preserving: no `fallback_builder` → their current
ephemeral-error path). **Games stays** (its `handle_select` has extra dropdown-legacy guards + the
in-place fallback); its migration is a noted U3 follow-on — the shared button already supports its
fallback shape, so it's a drop-in later.

Contained to the held-set `hub_children.py` (safe — no active fleet) + the 2 hubs' files + tests.
Also GC'd the stale phase0 claim earlier in the chain.
