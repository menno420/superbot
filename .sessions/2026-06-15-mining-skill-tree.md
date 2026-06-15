# Session: mining §7.4 — the capped skill tree (Slice D)

> **Status:** `in-progress` — born-red session card (Q-0133). Flipped to `complete` as the final step.

**Branch:** `claude/mining-skill-tree-2026-06-15` · **Date:** 2026-06-15 · **Type:** product (S1 games / mining)

## What I'm about to do

Execute **Slice D** (the marquee) of `docs/planning/mining-structures-skill-tree-plan-2026-06-14.md`:
the **§7.4 capped skill tree** — the real Phase-2 build (the continuation Hermes opened #888 for but
didn't actually build; #888 closed as churn, the `continue` night-executor routine didn't fire).

Four branches (mining · combat · fortune · crafting), **capped so you can't max all** (forced
specialization), spending shared **game-XP**-derived points, folding into the shared `EffectiveStats`,
with a **coin-sink respec**. **Additive** — empty allocations → byte-identical (the safety invariant);
combat (deathmatch) is left untouched this slice (a documented follow-up). The mining branch is **wired
into mine loot** (the concrete gameplay effect); all four branches' bonuses show on the character/gear
panels.

Files: migration 071 · `utils/db/games/player_skills.py` · `utils/mining/skills.py` (pure) ·
`services/skill_service.py` · the `EffectiveStats` merge at the mining read sites ·
`!skills`/`!skill`/`!respec` · the RS02 ratchet for the new write primitive · tests + a real-Postgres boot.

(Close-out + enders + badge flip at the bottom as the final step.)
