# 2026-06-20 — Creature game: playability simulator + design + copyright

> **Status:** `in-progress`

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

(In-progress; flipped to `complete` as the final step.)

## ⚠️ Process note (Q-0102 input — own mistake)

Ran `git reset --hard origin/main` to sync the branch **before committing** the working-tree
changes — discarded the edits to 3 tracked files (the untracked new files survived). Re-applied
them. **Lesson:** commit (or stash) before any `reset --hard`; when syncing a post-squash branch,
prefer creating a fresh branch off `main` over resetting a dirty tree.
