# Session — fishing ecosystem #2, PR 1 (the core loop)

> **Status:** `in-progress`

## What I'm about to do (born-red declaration, Q-0133)

Scheduled dispatch, **empty work order** → the live ▶ Next action: the idea→plan
gate is open (Q-0172) and the canonical first candidate is **fishing**, the
owner-ratified ecosystem #2 (V-13/Q-0090) that never became a plan. Self-initiated
promotion (flagged on the run-report ⚑ Self-initiated line).

**Planned (this PR):** the fishing core loop, mirroring the mining decomposition
exactly (`docs/planning/fishing-ecosystem-plan-2026-06-18.md` PR 1):

1. `docs/planning/fishing-ecosystem-plan-2026-06-18.md` — the synthesized plan.
2. `utils/fishing/` — pure domain (`fish.py` species catalog + `rewards.py` roll).
3. `migrations/075_fishing_catch_log.sql` — the per-(user,guild,species) collection log.
4. `utils/db/games/fishing.py` (+ `utils/db/__init__.py` wiring) — conn-aware CRUD.
5. `services/fishing_workflow.py` — `fish()`: roll → ONE txn (record catch + credit
   coins via the audited `economy_service` seam + award `GAME_FISHING` XP) → events.
6. `services/game_xp_service.py` — add `GAME_FISHING` + the `"fish"` award.
7. `cogs/fishing_cog.py` — `!fish` / `!fishlog` / `!fishtop` + Help hook + setup.
8. Registration: `subsystem_registry` (hub-less, Help-hooked) + `config.INITIAL_EXTENSIONS`
   + the doc surface maps.
9. Tests: domain + workflow + the enumeration touch-points stay green.

**Review gate:** a complete new ecosystem subsystem is **substantial** → label
`needs-hermes-review`, do NOT self-merge (Q-0117), matching the sibling #929/#941.

## What shipped

_(filled at close)_
