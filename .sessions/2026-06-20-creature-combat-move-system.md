# 2026-06-20 — Complete the creature plan: real moves, damage types, 6v6 teams (sim-validated)

> **Status:** `complete`

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

## Shipped (PR #1194)

- `creature_battle_sim.py` move system + 6v6 + AI policies + new checks; `test_creature_battle_sim.py`
  (+5 → 11); design doc §2b complete combat spec + §2/§3/§5 updates.

## Decisions made alone (owner gave the structure; I picked the knob values)

- **Move powers** Normal 9 / element 12, **buff +25%/cap +50%** — tuned so the element move beats
  Normal except vs resistances (the move-choice skill) and setup is worth a turn but not degenerate.
- **Status moves both modeled as self-buffs** (+DEF / +ATK) for v1; flagged the heal / enemy-DEF-down
  alternatives as the one open knob (§5) — owner picks the feel, sim re-validates.
- **Skill baseline = beginner (element-spam), not random** — the random strawman overstated the gap
  (93%); a realistic beginner gives a fun ~71%. The sim's own warn flag forced this correction.

## Flagged for maintainer

- **Status-move effect is the one open design knob** (§5): self-buff vs heal vs enemy-debuff. Tell me
  the feel you want and I'll swap + re-run (one-liner).
- Q-0187(a–d) confirmations still open; this builds on the recommended/owner-specified path.

## 💡 Session idea (Q-0089)

**A `--matchup A B` sim mode that prints a single annotated battle log for two named creatures.**
The owner is a visual designer; a "show me Cindling vs Abysscale, move by move" command would let him
*feel* a specific matchup (and the move-choice/setup AI) without reading aggregate win-rates. The
sample-battle code already exists — generalize it behind a flag. Pairs with the captured `--roster`
A/B-testing flag. Lane = tooling. (Captured, not built.)

## ⟲ Previous-session review (Q-0102)

The #1193 (data-driven catalog) session set this one up perfectly — because the roster was already
*data*, this session only had to extend the *engine*, not re-touch 36 creatures. That's the
data-driven payoff landing one session later, exactly as argued. **System improvement:** the sim is
now ~520 lines doing two jobs (combat engine + balance harness); when it graduates to
`services/creature_battle_engine.py` at the runtime build, the *engine* half should move and the
*harness* half stay in `tools/` — worth noting now so the split is clean later (added to the dock-in
§4 thinking).

## 📤 Run report

- **Did:** completed the combat plan — real moves/damage types/6v6, sim-validated · **Outcome:**
  shipped (design tooling + docs)
- **Shipped:** #1194 — move system + 6v6 + §2b combat spec
- **Run type:** `manual · owner-directed design (complete the plan)`
- **⚑ Owner decisions needed:** status-move effect knob (§5); Q-0187(a–d) still open
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** no (owner directed the move/type/team design explicitly)
- **↪ Next:** owner picks the status-move feel → sim re-validates; then the gated runtime build
  (Lane A catch, Q-0186) graduates engine math to `services/creature_battle_engine.py`.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session | 1 (#1194, design tooling + docs, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 |
| Combat model | stats-only 3v3 → 4-move / Normal-type / 6v6 with status buffs |
| Sim checks | 4 → 6 (added status-move value + full-team grind) |
| Tests | 6 → 11 (`tests/unit/tools/`) |
| Verdict | PLAYABLE on seeds 42/7/123/99 |
| Design trap caught by the sim | 1 (random baseline → 93%; rebaselined to beginner → ~71%) |
| New ideas contributed | 1 (sim `--matchup A B` annotated-log mode) |
