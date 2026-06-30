# 2026-06-30 — BTD6 boss-fight estimator (estimate, don't refuse)

> **Status:** `in-progress`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**Branch:** `claude/ai-answer-storage-plan-3fvdit` (restarted from main; PR #1572 merged).
**Run type:** manual (owner-directed).

## What I'm about to do

The owner, reviewing the review-log export, pointed out (correctly) that the bot **refuses
questions it has the data to estimate**: "how do I beat Bloonarius on Monkey Meadow / cheapest cost /
how long". The bot has boss HP + speed (`bosses.json`), per-crosspath combat stats
(`stats/*.json` — damage, attack rate, projectiles, MOAB/boss damage modifiers) and tower costs.
The only true gap is **track length** (`maps.json` has none — to be curated/approximated).

Owner picked **the full estimator** (~2-3 PRs): boss-kill time + cost + track-time gate + a
cheapest-tower-per-$/DPS ranking, giving an **estimate with stated assumptions** (he explicitly
accepts approximate over refusing).

**Design principle:** the arithmetic is **deterministic** (a compute service), not the model doing
mental math — the same pattern as the round-cash workflow / `deterministic_btd6_list_reply` (and the
fix for the haiku confabulation seen in the #1572 export).

Build order:
- **PR 1 (this card):** the deterministic estimator core — `services/btd6_estimator_service.py`
  (effective single-target boss DPS via the existing `btd6_stats_service.attack_breakdown`,
  cost-to-crosspath, time-to-kill = HP/DPS, DPS-per-dollar, a cheapest-counters ranking) + a
  `!btd6estimate` command to exercise it. Offline, fully unit-tested. No AI-path change yet.
- **PR 2:** curated per-map track-time table + the "does it escape" gate, and wiring the estimator
  into the BTD6 answer path (deterministic reply + an instruction so the model estimates instead of
  refusing).
