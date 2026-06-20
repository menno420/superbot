# 2026-06-20 — Creature game: playability simulator + design + copyright

> **Status:** `complete`

## Arc

Continuation of the Pokétwo lane. The owner asked for three things: *"use a simulator to see how
playable it is"*, *"PvP battles with the Pokémon would be great"*, and *"how is the copyright with
Pokémon names — can we use them or do we need to create our own?"* Owner also said *"you can pick
good defaults."* Deliverable: a runnable playability simulator for an original-creature catch +
PvP-battle game, a v1 design doc, the copyright answer, and the routed design decisions. Design
tooling + docs only — no `disbot/` runtime code.

## Plan (what this PR adds)

- `tools/game_sim/creature_battle_sim.py` — stdlib-only, deterministic Monte-Carlo simulator
  (type balance · raw-level dominance · normalized fairness · skill impact · catch grind +
  sample battle + verdict). Original creature roster (no Pokémon IP).
- `tests/unit/tools/test_creature_battle_sim.py` — smoke + invariant guard (engine unbiased; type
  chart symmetric; catch grind sane).
- `docs/planning/creature-game-design-and-sim-2026-06-20.md` — v1 ruleset, copyright decision
  (original creatures), the **PvP level-normalization** finding, sim results, dock-in plan.
- Feature-mapping plan: battle row GATED → DESIGNED (owner PvP greenlight) + creature callout.
- Router **Q-0187** (creature IP · PvP normalization · art); homed the new plan.

## Shipped (PR #1183, design-tooling + docs)

- **`tools/game_sim/creature_battle_sim.py`** — the playability simulator the owner asked for.
  Verdict at v1 numbers: **PLAYABLE (no flags)**. Surfaced the core design rule **PvP must be
  level-normalized** (raw +2 level gap wins ~100% → otherwise grind/whale = P2W, Q-0039).
- **`tests/unit/tools/test_creature_battle_sim.py`** — 6 guards (engine unbiased, type chart
  symmetric, raw-level dominance real, catch grind sane, `main()` runs).
- **`docs/planning/creature-game-design-and-sim-2026-06-20.md`** — v1 ruleset + copyright answer
  (original creatures) + sim findings + dock-in plan.
- Feature-mapping plan battle row GATED → DESIGNED; **Q-0187** routed (IP · PvP normalization ·
  art); homed the new plan.

Verification: sim runs green, `pytest tests/unit/tools/` 6/6, `check_quality --check-only` ✓,
`check_docs --strict` ✓, `check_plan_homing` ✓ (39/39 homed).

## Decisions made alone (owner said "pick good defaults")

- v1 ruleset numbers (6 elements, symmetric type chart, 12 creatures, MOVE_POWER/scaling) — tuned
  via the sim to land all fairness checks green. Reversible (numbers, not architecture).
- **Original creatures** (vs Pokémon names) — recommended in Q-0187; the sim roster is original.
- **Level-normalized PvP** — the sim's evidence-backed recommendation; routed for confirm.

## Flagged for maintainer

- **Q-0187** — confirm: original roster (recommended) · level-normalized PvP (recommended) · v1 art
  bar. None blocks the catch half (Lane A / Q-0186).

## 💡 Session idea (Q-0089)

**Keep a tiny `tools/game_sim/` harness as the standing "balance before build" gate for any new
game mechanic.** This sim caught a fun-killing flaw (level decides everything) in minutes, before a
line of `disbot/` was written — the cheapest possible place to find it. A light convention ("new
game/economy mechanic ships a Monte-Carlo balance sim + a fairness assertion first, like
gear-set-numbers did informally") would make playability a *checked* property, not a hope. Lane =
tooling/design. (Captured, not generalized this run.)

## ⟲ Previous-session review (Q-0102)

The previous run (#1182, the BUG-0019 note) correctly *routed* the AI-behavior fork instead of
patching the gated path — good discipline. **What this run did better than its own first instinct:**
I almost answered "battles are gated, can't do them" — but the owner-as-designer expressing intent
*is* the gate clearing, and a simulator let me de-risk it immediately rather than defer. **System
improvement:** my `git reset --hard` on a dirty tree (process note below) shows the post-squash
branch-sync step is a foot-gun; the workflow should prefer "branch fresh off main" over "reset the
working branch" after a squash-merge. Worth a one-line note in the session-close runbook.

## 📤 Run report

- **Did:** built a creature-game playability simulator + v1 design + copyright answer; routed the
  design decisions · **Outcome:** shipped (design tooling + docs)
- **Shipped:** #1183 — `creature_battle_sim.py` (verdict PLAYABLE) + design/sim plan + Q-0187
- **Run type:** `manual · owner-task (sim + design)`
- **⚑ Owner decisions needed:** Q-0187 (original roster · level-normalized PvP · art)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (owner-directed: simulator + PvP + copyright; design choices routed)
- **↪ Next:** on Q-0187 confirm → the creature-battle subsystem is a runtime session (the sim's
  math graduates into `services/creature_battle_engine.py`); catch half is Lane A / Q-0186

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#1183, design-tooling + docs, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 (sim is a `tools/` design tool, not runtime) |
| New tooling | 1 (creature playability simulator + 6 guard tests) |
| Design flaws caught by the sim | 1 (raw-level dominance → the PvP normalization rule) |
| CI-red rounds | 1 (by-design born-red session gate only) |
| New ideas contributed | 1 (`tools/game_sim/` as a standing balance-before-build gate) |

## ⚠️ Process note (Q-0102 input — own mistake)

Ran `git reset --hard origin/main` to sync the branch **before committing** the working-tree
changes — discarded the edits to 3 tracked files (the untracked new files survived). Re-applied
them. **Lesson:** commit (or stash) before any `reset --hard`; when syncing a post-squash branch,
prefer creating a fresh branch off `main` over resetting a dirty tree.
