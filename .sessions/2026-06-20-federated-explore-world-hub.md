# 2026-06-20 — Federated Explore world hub (spine PR 1)

> **Status:** `in-progress` — born-red session card (Q-0133). Flips to `complete` as the
> deliberate final step once the work + close-out docs land.

> **Run type:** routine · dispatch

## What I'm about to do

Build **PR 1 of the federated Explore-hub spine plan**
(`docs/planning/explore-hub-federated-world-plan-2026-06-19.md` §4) — the ungated keystone
slice named as a ▶ Next startable in `current-state.md`. This is a scheduled (empty-order)
dispatch fire; the buildable `ready` queue's top ungated item is this hub.

Scope (the "town square" spine):
- **NEW `services/world_registry.py`** — the world-registry seam: a small `WorldEntry`
  registry (`key/label/emoji/description/opener`) subsystems dock into. Pure: no view imports
  (stores opaque openers), so it respects the services-layer boundary.
- **NEW `views/explore/world_hub.py`** — `ExploreWorldHubView(HubView)` +
  `build_world_hub_embed()`, the top-level open-world hub that routes to each registered game
  (Mine → mining hub · Fish → fishing info card). Mirrors the proven `views/games/hub.py`
  registry-driven pattern.
- **EDIT `views/mining/main_panel.py`** — the mining `🗺️ Explore` button (`custom_id`
  `mining:explore_hub`, preserved) becomes a thin forward to the new world hub (re-parenting,
  per the plan). Existing players still get a panel.
- **RETIRE `views/mining/explore_hub.py`** (the 2026-06-15 pure stub it supersedes) + its test.
- **EDIT `cogs/games_cog.py`** — add the `!world` top-level command opening the world hub
  (`!explore` is taken by the hidden mining depth-event mechanic — distinct concept, not reused).
- **Tests:** registry register/de-dup/sort; world hub renders registered entries; mining
  forward; `!world` command.

Merge gate: this is a **SUBSTANTIAL plan step** (new view package + new service seam +
user-facing hub) → label **`needs-hermes-review`**, do NOT self-merge (Q-0117). It also wants
a runtime live-walk the autonomous session can't do.

PR 2 (global/per-game XP split) + PR 3 (cross-game identity card) stay for later runs; PR 1 is
the keystone the others read.
