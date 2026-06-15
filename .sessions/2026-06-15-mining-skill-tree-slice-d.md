# 2026-06-15 — mining Slice D: capped skill tree (§7.4)

> **Status:** `in-progress`

**Branch:** claude/mining-skill-tree-slice-d
**Type:** routine run — owner-directed product work (continue the mining plan)

## What I'm about to do

The owner clarified the dispatch: a light stale-docs touch, then **continue the mining plan**.
This is an owner-directed feature (not agent-originated), so the phase gate doesn't apply —
building the plan's recommended marquee slice:

**Slice D — Capped skill tree** (`docs/planning/mining-structures-skill-tree-plan-2026-06-14.md`):
four branches (mining/combat/fortune/crafting), per-branch cap 10, soft total cap 20 (< 4×10 ⇒
forced specialization), points derived from shared game-XP level. Allocate is self-service;
respec is a coin sink. Empty allocations stay byte-identical to today (the safety property).

- migration `071_player_skills.sql` + `utils/db/games/player_skills.py`
- pure `utils/mining/skills.py` (`skill_stats`) + `utils/mining/character.py` (`character_stats`)
- `services/skill_service.py` (available points / allocate / respec)
- merge into `mining_workflow.descend`
- `🌳 Skills` hub button + `!skills` command + `views/mining/skills_panel.py`
- boundary ratchet gains `set_skill_points`; tests; docs.

## Verification

`python3.10 scripts/check_quality.py --full` + `check_architecture.py --mode strict`; migration
count rises by 1 (071) — a new feature table (the work order's "migration count unchanged" was
written for a no-op docs slice; this is the real build).
