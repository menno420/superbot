# 2026-06-23 — Phase-0 completion: hub-child primitive + settings-orphan guard + fleet plan

> **Status:** `in-progress` — owner-directed: finish the Phase-0 rails so the ultracode consolidation
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

(Close-out enders written at session close.)
