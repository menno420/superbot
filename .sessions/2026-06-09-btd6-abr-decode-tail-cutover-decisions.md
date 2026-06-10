# 2026-06-09 — BTD6: ABR ingestion, decode tail, cutover decisions (PR #638)

**Task:** "map the rest of the dump" (direct maintainer request, v55.1 dump).
**Shipped:** PR #638 — three slices: (1) ABR + income sets game-natively ingested
(`abr_rounds.json` + `income_sets.json`, `roundset=` threading through service →
AI tools; DefaultRoundSet first parity-proven 140/140 vs committed `rounds.json`);
(2) decode tail closed — subtower mechanisms 7/7 (Alchemist `secondaryTowerModel`,
Beast leash ×2, Mini-Comanche + air-unit attacks, TranceTotem, PermaPhoenix,
expire-model lifespans), zone `inclusive` flag (Obyn's ×0.6 totem read *inverted*
without it), buffs 11→15 (range fraction semantics ×4-confirmed, radius, banana
income, projectile speed); (3) owner round captured + implemented — **Q-0066
dedicated cutover session next · Q-0067 Farm/Village FULL tiers (refined from
"minimal" in a same-evening re-ask) · Q-0068 per-tier beast names · Q-0069
projectile-speed +25% (implemented same session)**. Router §29; decode-status
start-here header routes the next session straight at the cutover.

## Process learnings (the durable part)

- **The remote container skips the format hook.** First push went CI-red on
  black. The PostToolUse auto-fix does not run here — `check_quality.py --full`
  before *every* push, not just the first.
- **Pipe-status trap:** `pytest … | tail -2 && git commit` commits on a red
  suite — the chain sees *tail's* exit 0. That pushed merge commit `ae6e14d`
  with a failing test. Either drop the pipe or test the PIPESTATUS.
- **GitHub Actions silently spawned no runs** for two consecutive pushes
  (b85def7/938328d — commits arrived, PR head moved, zero check runs, no error
  anywhere). An **empty-commit nudge** (`git commit --allow-empty`) re-fired the
  `pull_request: synchronize` event and everything ran. Check
  `actions_list`-by-branch when `get_check_runs` returns empty for >5 min.
- **4 sibling PRs merged mid-session** (#639 Lane 4, #640 Lane 7, #641, #642
  Lane 8 — the whole multi-lane queue completed tonight). Cost here: two
  roadmap at-a-glance UNION merges + **one semantic conflict git can't see** —
  #639's new `btd6_answerability` test pinned `alternate_round_sets` as an
  unsupported gap, written before this branch graduated ABR to a fixture; the
  pin moved to `abr_rounds`-is-a-fixture + `other_round_sets`-is-the-gap. When
  a sibling ships a *pin* against a surface you are changing, grep their merged
  tests for your domain's names after every main-merge.
- **Owner-round duplicate ask still paid:** Q-0066–69 got asked twice by
  mistake; the re-ask *refined* Q-0067 (minimal → FULL tiers). Recorded as
  two-round in the router with the second answer superseding.

## BTD6 facts pinned this session (for the cutover agent)

- `Rounds/` = 46 sets; only `AlternateRoundSet` is player-facing. ABR plays
  r3–r100, $650 start (per `Mods/Hard.json` — read, not assumed); r1–2 carry
  null cumulative + disclosure notes.
- No named-reference subtower morph exists in v55.1 (the Alchemist premise in
  older notes was wrong — it's the unread `secondaryTowerModel`).
- `FindDeploymentLocationModel` deliberately unwired (duplicate of Marine).
- Remaining 23 buff/zone types are provably unconfirmable pre-cutover — do not
  chase them before the towers land game-native.

## Grooming pass (Q-0015)

The session's slice 3 *was* the grooming outcome: the BTD6 cutover moved
idea → decided (Q-0066–Q-0069) → roadmap **Now** with a dedicated-session
route and a turn-key start-here header in
`docs/btd6/btd6-gamedata-decode-status.md`. No second idea touched — context
budget went to the lanes-7+8 merge reconciliations instead.

**Resume point:** next session = the `--all` towers cutover (Q-0066). Read
`docs/btd6/btd6-gamedata-decode-status.md` ⭐ header first; everything is
decided and unblocked once #638 merges.
