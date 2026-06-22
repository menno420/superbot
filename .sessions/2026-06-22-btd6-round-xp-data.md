# 2026-06-22 — BTD6 XP-per-round data (validated formula → round_xp.json)

> **Status:** `in-progress`

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
×0.30 through round 100 then ×0.10 on rounds 101+.

## Shipped

_(filling in)_
