# Agent Context Pack — Games

> **Status:** `reference` — generated orientation aid (NOT source of truth).
> Generated: 2026-06-10 · Subsystem key: `games`

> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.
> Canonical docs listed under *Binding docs* always win over this pack.
> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`.

## Folio (start here)

[`docs/subsystems/games.md`](../../../docs/subsystems/games.md) — canonical area index, debug router, current state, next candidates.

## Binding docs (read before editing)

- docs/architecture.md
- docs/ownership.md
- docs/runtime_contracts.md
- docs/decisions/002-game-state-not-restart-safe.md

## Reference docs (consult on demand)

- docs/archive/games-actionability-roadmap.md

## Likely source areas

- disbot/cogs/games_cog.py
- disbot/cogs/blackjack/
- disbot/cogs/blackjack_cog.py
- disbot/cogs/rps_tournament/
- disbot/cogs/rps_tournament_cog.py
- disbot/cogs/deathmatch/
- disbot/cogs/deathmatch_cog.py
- disbot/cogs/mining_cog.py
- disbot/utils/mining/
- disbot/services/mining_workflow.py
- disbot/services/game_xp_service.py
- disbot/cogs/counting/
- disbot/views/blackjack/
- disbot/views/rps/
- disbot/views/games/
- disbot/views/mining/
- disbot/services/game_state_service.py
- disbot/services/economy_service.py
- disbot/utils/db/games/

## Do NOT create

These systems already exist — duplicating them is the main source of
architectural drift in this repo.

- A Redis-backed game-state store — ADR-001 (no Redis) + ADR-002 (in-memory accepted)
- Any promise of restart-safe game state — ADR-002 is binding
- Economy side-effects outside the disbot/services/economy_service.py seam

## Active gates

- Game state is intentionally not restart-safe (ADR-002). Accepted behavior — not a proposal target.

## Verification commands

Run these before pushing any change to this subsystem:

```
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
python3.10 -m pytest tests/unit/ -x -q -k game
```

---

*This pack is orientation only.  When this file and a canonical doc
disagree, the canonical doc wins.  When this file and source code
disagree, source code wins.*
