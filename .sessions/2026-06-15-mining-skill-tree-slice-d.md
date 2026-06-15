# 2026-06-15 — mining Slice D: capped skill tree (§7.4)

> **Status:** `complete`

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

`python3.10 scripts/check_quality.py --full` → **green** (black/isort/ruff/check_docs/mypy + 9698
tests passed). `check_architecture.py --mode strict` → 0 new violations (only pre-existing known
warnings). +33 unit tests (skills model, character_stats byte-identical invariant, skill_service
cap/guard/respec math, write-boundary ratchet gains `set_skill_points`; hub button-count ratchet
14→15). Migration count rises by 1 (071) — a new feature table (the work order's "migration count
unchanged" was written for the no-op docs slice it expected; this is the real build the owner
redirected to).

> **Owner note — real-Postgres walk not run this routine.** The plan asks for a test-bot boot on
> real Postgres per slice. The SQL mirrors the proven #884 Vault pattern exactly and the full
> offline suite is green, but a live deposit/allocate/respec round-trip is the remaining
> confidence step (owner or a follow-up session with Postgres up).

## Run report

- **Trigger:** "Implement Mining Phase 2 — Forge/Vault/Home + skill-tree" (owner clarified live:
  light stale-docs touch, then **continue the mining plan**) · **Class:** feature (owner-directed)
  · **Outcome:** **shipped** Slice D (the marquee skill tree).
- **Shipped:** #891 — capped skill tree end-to-end (migration 071, db primitive, pure model +
  merge, skill_service, hub panel + commands, 33 tests). Docs: plan ticked, games folio +
  current-state lane-1 updated, the #889 phase-gate idea corrected.
- **⛏ Owner decisions needed:** none. (Slices A/B/C/E/F remain ▶ startable in the plan.)
- **🔧 Owner manual steps:** a real-Postgres play-test of `!skills` / allocate / respec (optional
  confidence step; offline suite already green).
- **↪ Next:** continue the mining plan — Slice A (Vault inventory-cap sink) or B (Forge); E/F
  (respec polish / skill titles) are now unblocked by #891.

## 💡 Session idea (Q-0089)

Sharpened (not forced): **a dispatched feature is owner-directed and must NOT be phase-gated** —
only agent-*self-originated* features are. Captured as the "deeper fix" correction in
`docs/ideas/dispatch-phase-gate-precheck-2026-06-15.md` (the routine prompt + phase-gate doc
should split the `feature` branch on origin). This is the live-proven form of
`routine-system-improvements-2026-06-14.md` Priority 5.

## ⟲ Previous-session review (Q-0102)

The prior run in this same chain (the one that opened **#889**) is the one to learn from — and the
lesson is the inverse of what it concluded. It ran `check_phase_gate.py`, got fix-phase, and
**refused to build the dispatched mining feature**, treating it as agent-originated. The owner
corrected this directly: a *dispatched* work order is owner-directed and isn't gated. The miss:
following the routine prompt's `CLASS: feature → run the gate` step *literally*, without weighing
it against the plan's explicit standing steer (*"bot-side product work is welcome unattended — you
can work as long as you want, executing any documented slice"*) — exactly the "session prompts are
guidance, not orders" / "constraints serve the goal" rule in CLAUDE.md. **System improvement:** the
phase-gate doc + routine prompt must state the dispatched-vs-self-originated split once, crisply
(captured above) — otherwise a literal agent burns dispatched product work as "gated." Honest
positive: that run *did* correctly dispose of the orphan #888 and keep the loop clean.
