# 2026-06-22 — BTD6 XP-per-round data (validated formula → round_xp.json)

> **Status:** `complete`

Owner-directed. The maintainer asked whether XP-per-round is stored as data and,
if not, to find where the dump stores it and write a parser. Finding: it is
**not** stored, and the raw dump has **no XP field** on rounds or bloons (verified
against a fresh clone of Btd6ModHelper/btd6-game-data). XP per round is a
*derived* quantity. Per the owner's choice (AskUserQuestion: "validate against a
source first"), the formula was validated against bloonswiki.com before writing
any numbers.

## Validated formula (bloonswiki.com, confirmed vs the "Base XP" round-table column)

Base XP earned per round `r` (before difficulty / freeplay / Monkey Knowledge
modifiers):

```
XP(r) = 20·r + 20          for r ≤ 20
XP(r) = 40·(r − 20) + 420   for 21 ≤ r ≤ 50
XP(r) = 90·(r − 50) + 1620  for r ≥ 51
```

Empirically matched against the wiki's own `Base XP` column at every band
boundary (r = 1, 2, 5, 10, 19, 20, 21, 22, 49, 50, 51, 52, 99, 100). Modifiers:
difficulty ×1.0/1.1/1.2/1.3 (Beginner/Intermediate/Advanced/Expert), freeplay
×0.30 through round 100 then ×0.10 on rounds 101+. The per-tower split (by share
of cash invested) and MK bonuses are gameplay-dependent → not stored.

## Shipped

- **`scripts/parse_gamedata.py`** — `_round_base_xp(r)` (the validated piecewise
  formula) + `build_round_xp()` generator (pure formula — needs neither the dump
  nor the network; stamps `game_version` from the committed `rounds.json`) +
  `--round-xp` CLI dispatch.
- **`disbot/data/btd6/round_xp.json`** — base XP for rounds 1–140 (covers ABR's
  full range; standard play is 1–100) + `difficulty_multipliers` +
  `freeplay_multipliers` + a full `xp_source` provenance string documenting that
  the dump has no XP and how the formula was validated.
- **`disbot/services/btd6_data_service.py`** — `RoundXpEntry` dataclass;
  `round_xp.json` registered as an optional fixture and loaded in `_load_dataset`
  (uniqueness-checked, source recorded); `BTD6DataSet.round_xp` +
  `xp_difficulty_multipliers` + `xp_freeplay_multipliers`; helpers
  `round_base_xp(n)` and `round_xp_earned(n, difficulty=…, freeplay=…)`.
- **`tests/unit/services/test_btd6_round_xp.py`** — pins the formula against the
  wiki `Base XP` oracle at every band boundary, the generated payload, a
  committed-file-vs-generator drift guard, the runtime loader, and the
  difficulty/freeplay modifier math.

Verified: `round_xp` + data-service suites green (68 passed); `mypy
btd6_data_service` clean; `check_architecture --mode strict` 0 errors (pre-existing
view WARNs only); regenerated `round_xp.json` matches the wiki values.

## ⚑ Self-initiated

No — owner-directed (the maintainer asked the question and chose the
"validate-against-a-source-first" path via AskUserQuestion). PR #1318 opened
born-red → flipped ready; auto-merge armed (Q-0191 owner-directed → merge on
green).

## 💡 Session idea (Q-0089)

**Add per-round XP to the existing round Q&A surface (deterministic reply +
embed).** This PR shipped the *data*; the natural next step is letting the bot
answer "how much XP does round 63 give?" and showing XP alongside RBE/cash in the
round embed (the wiki presents Base RBE / Base cash / Base XP together — our embed
already has the first two). A small `deterministic_round_xp_reply` in the BUG-0009
floor family, grounded on `round_xp_earned`, would do it. Genuine and scoped: the
data + helpers landed here make it a thin follow-up, and it directly extends a
feature players already use.

## ⟲ Previous-session review (Q-0102)

The previous session (#1316, "list all monkey knowledge") correctly identified
the all-tabs roster gap and fixed it narrowly, and its log flagged the recurring
"scoped builder, no un-scoped branch" class with a coverage-guard idea — good
self-auditing. What both that session and this one underline as a *system*
improvement: the BTD6 data layer keeps growing one derived quantity at a time
(cash, then XP), each validated against a different external oracle (cyberquincy
for cash, bloonswiki Base-XP column for XP). Worth a small **`docs/subsystems`
note enumerating the derived round quantities + their validation oracle**, so the
next agent adding (say) per-round lives or income knows the pattern and the
"validate against a named source, pin it in a test" discipline without
rediscovering it. Recorded as a grooming candidate.

## 🔎 Doc audit (Q-0104)

- `check_quality --full` ✓ · `check_architecture --mode strict` 0 errors.
- New owner decision: the maintainer's AskUserQuestion choice ("validate against a
  source first") is recorded here in the session log; it's a one-off task
  direction, not a standing policy, so no question-router Q-block.
- No `current-state` ledger touch — recorded by the auto-triggered Q-0107
  reconciliation pass. Unmerged PR #1318 correctly absent.
- `round_xp.json` provenance is self-documenting (`xp_source`); the parser +
  dataclass + tests cross-reference each other and the wiki source, so no
  separate doc is required for this slice (the derived-quantities subsystem note
  above is filed as a grooming idea, not a gap this PR leaves open).

## Context delta

- **Needed but not pointed to:** that the BTD Mod Helper dump stores **no** XP
  *and* no per-bloon cash — cash (and hence any XP) is derived. The existing
  `cash_source` provenance hinted at it, but a one-line "the dump has no XP;
  round/economy values are derived, validated against named external oracles"
  note in the btd6 subsystem doc would have saved the dump-cloning verification
  step. (Filed as the Q-0102 system idea.)
- **Pointed to but didn't need:** the dump itself — `build_round_xp` is pure
  formula, so the clone was only needed to *prove the negative* (no XP field),
  not to generate the data.
