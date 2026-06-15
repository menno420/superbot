# Session — 2026-06-15 · mining Slice C — the Home structure (character-card backdrop)

> **Status:** `in-progress`

## What I'm about to do

Dispatch routine, fresh resume (clean budget). Both prior PRs this session (#906 log-triage,
#907 handoff) merged. Taking the next ▶ startable slice from my own handoff: **mining Home
(Slice C)** of [`mining-structures-skill-tree-plan-2026-06-14.md`](../docs/planning/mining-structures-skill-tree-plan-2026-06-14.md).
Unblocked by #905 (the generic `mining_structures` table + `build_structure` exist); **no open PRs**
so zero collision. Owner-steered mining product lane.

**A built Home structure (coin + material sink) that personalizes the Character card** — v1 is
**art-light** per the plan (a backdrop colour by Home level, *not* sprites — so it is NOT the
owner-blocked V-16 phase-2 PNG work). Additive: Home level 0 (unbuilt) renders byte-identical to
today.

- `utils/mining/structures.py` — add `HOME` + its 3-level build ladder + **generic**
  `build_cost` / `level_name` / `max_level` / `display_name` (per-structure registry); forge
  helpers delegate so #905's forge behaviour stays byte-identical.
- `services/mining_workflow.build_structure` — generalize the forge-specific messages to the
  structure's display name + a per-structure build reason (`market.HOME_BUILD_REASON`); forge
  output unchanged.
- `utils/character_render.py` — `CharacterSpec.backdrop` (default `None` → today's `_BG`,
  byte-identical) + `home_backdrop(level)` palette; wired through `build_character_spec` /
  `render_character_for(..., home_level=)`.
- Render call-sites (`views/mining/gear_panel.py` · `cogs/mining_cog.py` character card) read the
  Home level and pass it.
- UI — `views/mining/home_panel.py` (`MiningHomeView` + `build_home_embed`, mirrors the forge
  panel) + a `🏠 Home` hub button (row 4, beside Forge) + `!home` command.
- Numbers pinned in `docs/planning/home-numbers-2026-06-15.md` + unit tests
  (`tests/unit/utils/test_mining_structures.py` home cases · render byte-identical-when-0).

Verify: `check_quality --full` green + `check_architecture --mode strict` 0.
