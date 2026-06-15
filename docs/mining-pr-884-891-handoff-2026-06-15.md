# 2026-06-15 — mining PR 884/891 handoff

> **Status:** `complete`
> **Branch:** `docs/mining-pr-884-891-handoff-2026-06-15`
> **Linked docs PR:** #none yet — needs branch push + `gh pr create`

## What landed (verified live 2026-06-15)

- PR **#884** (`claude/exciting-brahmagupta-1duzde` → `main`, merged ~00:11 UTC): **the §7.5 Vault** — per-player safe stash; `!vault` / `!stash` / `!unstash` atomic workflow through `services/mining_workflow.py` (RS02/Q-0071); additive-only, no existing inventory behaviour changed.
- PR **#891** (`claude/mining-skill-tree-slice-d` → `main`, merged 2026-06-15T01:05:46Z): **Mining Slice D — capped skill tree (§7.4)** — migration `071_player_skills.sql`, `utils/mining/skills.py`, `services/skill_service.py` (allocate/available/respec), `utils/equipment.py` `EffectiveStats` merge, `views/mining/skills_panel.py`, `!skills`/`!skill <branch>`.
  - Born-red card: opened `4f6a0e22`, flipped to complete `f733407c`.
  - Plan authority: the session card `docs/planning/mining-structures-skill-tree-plan-2026-06-14.md` is not carried forward as a committed file — it was reconstructed from PR 884's body; the canonical planner still names the plan at that path. A future docs session should either re-commit the plan or retire the path reference.

## Verified state

- **Open PRs:** zero in the mining lane.
- **Local state:** checked out on `docs/mining-pr-884-891-handoff-2026-06-15`, working tree clean.
- **Quality gates on #891:** `check_quality.py --full` green, `check_architecture.py --mode strict` 0 errors, byte-identical-when-empty invariant satisfied (as recorded in session log `f733407c`).

## Continuation options (next session does NOT autoselect)

Both options come from the canonical plan that drove Slice D. Pick ONE per session.

| Option | Description | Recommended when |
|--------|-------------|-------------------|
| **A — Vault v2 inventory soft-cap** | A small follow-up to #884: introduce the soft-cap that makes the Vault a sink (not free overflow). Documented in `docs/ideas/mining_exploration_brainstorm.md` §7.5 as a follow-up to §7.5 base ship. | You want a contained, additive slice ship before Forge/§7.4 respec work; lowest cross-cutting risk. |
| **Slice E — Respec service / cap enforcement** | Build the respec leg of the skill tree (`services/skill_service.py` respec path, atomic point-refund + re-allocate). This is the §7.4 complement to Slice D and the next item visible in the 01:05Z merge record. | You want to keep momentum on the §7.4 track. |
| **Slice B/F/G — Forge / Home (§7.5)** | The three structure families the owner has named as a planned slice set: Forge (tier-gated smelt/craft pipeline) + Home (hub backdrop, optional rest bonus) following the Vault milestone. | Forge dominates the remaining §7.5 surface; Home is the lightest of the three. The brainstorm (`docs/ideas/mining_exploration_brainstorm.md §7.7`) is the source of truth for the three-structure plan. |

## What this dispatch delivers

- One docs-only handoff PR on `docs/mining-pr-884-891-handoff-2026-06-15` that records:
  - what #884 and #891 shipped
  - verified state + gate results
  - the three continuation options with explicit discriminators so the next session doesn't have to reconstruct context from git log and IRC.

## open questions

- The canonical plan file `docs/planning/mining-structures-skill-tree-plan-2026-06-14.md` is referenced by name but not found on disk at session start. It was likely authored inside the PR 884 branch only. The next session that begins Slice E/B/F/G should **re-commit the plan to `docs/planning/`** before dispatching; the session card for this handoff noted that risk.
- Slice D was primarily an offline-only slice the Session log says real-Postgres smoke is optional); Forge/Home will likely need live verification. The night session should make that explicit in the work order.

## What this session deliberately did NOT do

- Did NOT open a new mining issue on GitHub (outside the docs-only PR write scope).
- Did NOT re-write current-state.md (requires separate branch + merge; needs human calibration against the live ledger).
- Did NOT dispatch a Claude Code routine — this doc is the handoff prerequisite, then the next cron / Hermes session dispatches.
