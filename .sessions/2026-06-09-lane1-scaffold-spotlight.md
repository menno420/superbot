# 2026-06-09 — Execution-plan Lane 1: new_subsystem.py scaffold + Spotlight registration

Same working session as `2026-06-09-multi-lane-execution-workshop-durability.md`,
continued after the maintainer (a) merged the parallel gate-lifting interview (the
merge conflicts this session resolved), (b) answered Q-0054 + the remaining
structured choices interactively, and (c) chose "Start Lane 1 anyway" with the
remaining context. Mining PR **#624** merged mid-session.

## Shipped (PR #626, draft→ready per Q-0052)

- **`scripts/new_subsystem.py`** (Q-0025): `check` verifies every registration
  touch-point (exit 1 on gaps), `scaffold` prints paste-ready snippets — edits
  nothing by design (generation is guessable; verification is not). 9 tests incl.
  a first-consumer regression net pinning Spotlight's full wiring.
- **Community Spotlight registered** (Q-0044): SUBSYSTEMS entry + community-hub
  `primary_children` + KNOWN_PANEL_COMMANDS + `build_help_menu_view` hook + the
  three doc rows; surface-map §3 banner resolved. Hub/view pins updated for six
  community children.

## Verification

Scaffold check all-green · CI mirror **8402 passed** (+9) · arch 0 errors · clean
boot (validate_registry OK; `discover_community_children()` →
`['xp', 'community_spotlight', 'role']`).

## Context delta

- **Needed but not pointed to:** the execution plan's "verified" Lane-1 touch-point
  list was one short — the parent hub's `primary_children` tuple is pinned equal to
  the parent_hub filter by `test_every_hub_primary_children_match_parent_hub_filter`.
  Now encoded in the scaffold (`hub-primary-children`) + noted on the plan's Lane 1.
- **Discovered by hand:** `cog_name_to_subsystem` lives in
  `core/runtime/command_surface_ledger.py` (not `utils/subsystem_registry.py` as the
  plan implies) and returns **None for unregistered keys** — pre-registration tooling
  needs the raw derivation (the scaffold reuses the ledger's own regexes).
- **Pointed to but didn't need:** nothing notable; the lane card's read-first list
  was otherwise accurate.
