# 2026-06-20 — Complete the creature plan: real moves, damage types, 6v6 teams (sim-validated)

> **Status:** `in-progress`

## Arc

Owner direction (in-session): *"make sure the plan is complete — there should be some real moves
with real damage types etc. 6 types to start; the '6 Pokémon team' as the standard, one of each
type; each creature has 4 attacks: 2 damage (one Normal type, one the special/element type) and 1
defensive + 1 offensive non-damage move."* This fleshes the combat model into a complete, validated
spec. Design tooling + docs only — no `disbot/` runtime.

## What this PR adds

- **`creature_battle_sim.py` — full move system:**
  - **Normal damage type** (always ×1.0) alongside the 6 elements.
  - **4 moves per creature**: Strike (Normal dmg, pow 9) · signature (element dmg, pow 12, type
    chart) · Bulwark (+DEF) · Onslaught (+ATK). Status buffs +25%/use, cap +50%.
  - **6v6 battles**, standard team = **one of each element**.
  - **Move-selection AI** (best-damage · naive-element · random · setup) — move choice + setup are
    the skill levers.
  - New checks: **status-move value** + a **6-mon standard-team grind**; skill-impact rebaselined to
    a realistic beginner.
- **`test_creature_battle_sim.py`** — +5 tests (Normal neutrality, 4-move structure, buff cap,
  status value, skill-vs-beginner band).
- **Design doc** — new **§2b** complete combat spec (types · teams · moves table · skill rationale ·
  the open status-move knob) + §2/§3/§5 updated with the new model + results.

## Verification (sim is PLAYABLE on seeds 42/7/123/99)

- Type balance 50.0–50.6% (spread 0.6pt) · normalized 6v6 ~51% · **skill impact ~71%** (target
  52–80) · **status value ~55%** (target 50–72) · starter grind ~7, full one-of-each-element team
  ~41 at L1. `pytest tests/unit/tools/` 11/11; `check_quality --check-only` / `check_docs --strict`
  / `check_plan_homing` green.
- **The sim caught a real trap:** vs a *random-move* opponent the skilled side won 93% (too
  absolute — random wastes turns buffing); rebaselining to a beginner (element-spam) gave a fun ~71%.

## Shipped

_(filled at close)_
