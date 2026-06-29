# 2026-06-29 — Farm leaderboard provider (completion-first deepening)

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did
Empty-fire dispatch advancing the S1 completion-first arc (Q-0209). The Leaderboards
completion assessment flagged "missing providers for several existing games"; Fishing
shipped as the worked example (#1540). This run shipped the **Farm leaderboard provider**
(rank by flock size) — the one remaining named game with a persisted per-player stat —
and **honestly documented why the other three can't get a turn-key board.**

**PR #1542 — one focused deepening slice.**

### Farm leaderboard provider
- **`top_farmers` db primitive** (`utils/db/games/farm.py`) — `[(user_id, chickens, coop_level)]`,
  `ORDER BY chickens DESC, coop_level DESC`, excludes 0-hen rows. SQL-shape pinned.
- **`FarmProvider`** (`services/rank_providers.py`) mirrors `FishingProvider`/`CreaturesProvider`:
  ranks by flock size (the durable "biggest farm" stat — stored `eggs` is the momentary unsettled
  faucet, deliberately not ranked), label `**Name** — N hens (coop Lv M)`, singular/plural "hen",
  structured projection for the image card. Registered + aliases `farmlb`/`farming`/`chickenlb`;
  cog docstring/help/command alias updated.
- **`harvest` card theme** (`utils/card_render.py`) — a warm wheat-gold/green field skin so the farm
  board reads distinct from `verdant`'s forest-green collection skin (the engine's "a new look = a few
  RGB tuples" property; the `test_every_theme_renders` loop covers it automatically).
- **Tests:** +6 provider tests (`test_rank_providers.py`: flock/coop render, singular hen, cap-at-10,
  on/off-board member_rank, deep-list limit=500, alias resolution) + 2 db SQL-shape pins
  (`tests/unit/db/test_farm_db.py`) + the registry-set test updated.

### Honest scope boundary (the investigation's real value)
Of the four games the assessment named, **only Farm has a persisted per-player rankable stat.**
**Blackjack** (in-memory game state; coins only via `economy_audit_log`), **Casino/poker** (ephemeral
play-chips, zero persistence), and **Word-Chain** (per-channel `chain_count`, no per-user tracking)
would each need a **migration + a write-path** before a board is possible — *not* turn-key. Documented
in S1 so a later session doesn't re-chase them as quick provider wins; they're a deepening *feature*
(add tracking → board), not a provider add. **The turn-key leaderboard-provider lane is now exhausted.**

## Verification
- `check_quality.py --full` GREEN after fixing two CI-only drifts the change introduced: a ruff F401
  (added `top_farmers` to `db.__all__`) and the committed `botsite/data/site.json` + `data.js` drift
  (the new `farmlb` alias changed the scanned command surface — regenerated via
  `export_dashboard_data.py --targets site`; the BUG-0018-adjacent generated-artifact class). 13009
  tests pass. `check_architecture --mode strict` 0 errors (pre-existing tracked warnings only).
  Committed-artifact sync tests (BUG-0022/0018 class) green.
- Born-red gate dogfooded: CI held #1542 red while the card was `in-progress` (the BUG-0027 fix
  working as intended), flips green on this `complete` push.

## 💡 Session idea (Q-0089)
**A `RankProvider`-coverage checklist generator** — a small read-only script that, for each game/economy
subsystem, reports whether it (a) is registered as a leaderboard provider and (b) has a persisted
per-player rankable stat (a `utils/db` top-N read). It would have produced this run's Blackjack/Casino/
Word-Chain finding mechanically instead of by hand, and would flag the *next* unprovidered game the
moment one is added — turning "which games are missing leaderboards?" from a manual assessment into a
one-command answer. Genuinely tied to this run (the assessment finding it automates) and cheap
(stdlib + the existing registry). Routed as an idea, not a unilateral checker (a CI-wired guard is a
judgment call; this is a convenience report).

## ⟲ Previous-session review (Q-0102)
The previous dispatch run (2026-06-28, RPS/Deathmatch/Chicken-farm certs + BUG-0027 gate fix) did
strong work — it caught and root-fixed a real workflow-integrity bug from its own behavior, and used a
disambiguated slug (`…-games-and-gate-fix.md`) precisely *because* it had just been bitten by the
collision. **What it did well that this run benefited from:** the completion-first assessment format it
established made the "which games lack leaderboards" finding already-scoped, so this run could go
straight to building. **Minor miss:** the assessment listed "Blackjack/Casino/Word-Chain/Farm
leaderboard provider" as four equivalent turn-key wins without checking each had a *persisted* rankable
stat — three of the four don't, which this run had to discover. **System improvement surfaced:** the
Q-0089 provider-coverage checklist above would make a future assessment state the persistence precondition
up front, so a "turn-key win" list never includes items that secretly need a migration.

## Doc audit (Q-0104)
Durable homes updated: S1 ▶ Next (Farm shipped #1542; remaining-games scope boundary documented;
turn-key provider lane marked exhausted) + S1 Recently-shipped. `current-state.md` Recently-shipped
untouched (PR #1542 not yet merged — the reconciliation routine records it; recon lane at #1530,
Q-0124). No new owner *decision* (a deepening feature, owner-greenlit lane). No bug-book change
(no bug surfaced). Claim file deleted at close.

## 📤 Run report
- **Did:** shipped the Farm leaderboard provider (`top_farmers` + `FarmProvider` + `harvest` theme +
  8 tests) and documented why Blackjack/Casino/Word-Chain can't get a turn-key board. · **Outcome:**
  shipped (PR #1542)
- **Shipped:** PR #1542 — `db.top_farmers`; `FarmProvider` + aliases + registry; `harvest` card theme;
  leaderboard cog help/aliases; `tests/unit/db/test_farm_db.py` + farm provider tests; regenerated
  `site.json`/`data.js`.
- **Run type:** routine · dispatch
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none (no migration; live on the next auto-deploy).
- **⚑ Self-initiated:** none — this is the dispatched completion-first ▶ Next plan slice (a *deepening*
  win on an existing feature, the worked example being Fishing #1540). No new feature invented; no
  unprompted promotion.
- **↪ Next:** the turn-key leaderboard-provider lane is **exhausted** (Fishing #1540 + Farm #1542). Next
  S1 completion-first work: **assess the remaining server-fns** (Counters · Spotlight · Channels · Setup
  wizard · AI · Logging · Diagnostics · Help · Admin · Inventory · Treasury · Cleanup · Automod ·
  Image-moderation · Security · Proof-channel · Utility — one cert each from `rubric-server-function.md`),
  **or** take the **Blackjack/Casino/Word-Chain leaderboard as a deepening *feature*** (migration +
  per-player W/L or score tracking on the audited settle path → then a provider — note Blackjack touches
  the settle-once money-safety guards, so size it carefully). Bug-book: BUG-0009/0011/0019#1 stay OPEN.
