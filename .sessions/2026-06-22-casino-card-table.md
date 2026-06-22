# 2026-06-22 — Casino subsystem: multiplayer card-game table framework + Texas Hold'em poker

> **Status:** `complete`

## What shipped (PR #1333)

Owner-directed (asleep, "card games like poker, playable in a group, each player gets their own
auto-updating ephemeral message… lean towards a Casino panel under Games… research / run a
simulator… surprise me"). Delivered end-to-end:

1. **Research + simulator** — `tools/sim/casino_games_sim.py`: a Discord-fit scorecard
   (group / private-info / simultaneity / latency-safety / depth / cost) that picked **Texas
   Hold'em** as the marquee, **and** a Monte-Carlo that validates the real engine (chip
   conservation across 8000 random all-in hands; 7-card showdown frequencies match known odds).
2. **Reusable pure primitives** — `utils/cards/` (ordered, rankable `Card`/`Deck`) and
   `utils/poker/` (`evaluate.py` best-5-of-7 scoring + `engine.py` the Hold'em state machine:
   blinds, BB option, all-ins, **side pots**, showdown). Discord-free, **57 unit tests**.
3. **Per-player auto-updating ephemeral table** — `views/casino/poker_table.py`: each seat's
   `InteractionMessage` handle is kept at Join; every state change re-renders + edits *every*
   seat's private panel plus the public board. Per-turn idle clock auto-checks/folds AFK seats.
4. **Casino hub** under Games — `views/casino/hub.py` + `cogs/casino_cog.py` (`!casino`/`!poker`);
   registry + `hub_registry` wired; roulette is a "coming soon" tile.

**Money:** v1 is **play-chips** (no economy seam) — real-coin N-party-escrow buy-in is a
documented follow-up. ADR-002 respected (in-flight state not restart-safe).

## Verification
- `python3.10 scripts/check_quality.py --full` green (lint + mypy `disbot/` + full pytest).
- `python3.10 scripts/check_architecture.py --mode strict` exit 0 (game-views allowlisted in
  `canonical_helpers.yaml` + `check_consistency.py`, mirroring rps/blackjack).
- Regenerated committed artifacts (dashboard.json / site.json / extension-crosswalk / env-vars
  doc) + updated the registry-drift surfaces a new subsystem trips.

## Decisions made alone (ratify if you disagree)
- **Play-chips, not real coins, for v1.** Real-coin multi-party pots need N-party escrow
  (`game_wager_workflow`); shipping that under "surprise me, going to sleep" was too money-risky.
  Real-coin buy-in is the top follow-up.
- **Casino as its own Games-hub child** (not folding blackjack in). Blackjack keeps its own
  entry; Casino is the home for *group* games + future roulette — matches the owner's "casino
  panel so it can include roulette" lean.
- **Texas Hold'em first** (over a simpler game) — it's what you named and the sim confirms it's
  the one game that justifies the whole per-player-ephemeral framework.

## Flagged for maintainer (known limits / unverified)
- **Not live-verified on real Discord** — the ephemeral broadcast + 15-min webhook-token refresh
  is sound in principle and unit-tested at the render layer, but the multi-client live feel
  (latency of N simultaneous ephemeral edits, token edge cases) wants a real table test. This is
  the #1 thing to check in prod.
- Raise UI is min / pot / all-in quick buttons (no custom-amount modal yet).
- One table per channel; no rebuy mid-table.

## 💡 Session idea
**A generic `MultiplayerEphemeralSession` primitive in `core/runtime/`.** The poker table's
"shared state + keep each participant's ephemeral handle + broadcast-edit-all on change" is a
genuinely reusable Discord pattern (roulette, multiplayer blackjack, co-op quests, voting all want
it). Extract it on the rule of three (poker + roulette + one more). Filed mentally as the
follow-up #5 in the design doc; worth a `docs/ideas/` entry when roulette is picked up.

## ⟲ Previous-session review
The prior session (fishing **bait layer**, #1329) was a clean, well-scoped economy-knob add on an
existing seam — good discipline (pure tunables, migration, panel). What it (and the fishing arc
generally) shows is a **rule-of-three forming across games**: fishing, mining, farm, and now poker
each re-implement "in-memory game session + render + per-channel registry". *System improvement
this surfaces:* the games folio should grow a short **"shared game-session patterns"** note so the
next game-builder reuses rather than re-derives — and the `MultiplayerEphemeralSession` extraction
above is the concrete first step. (Added a renderer/broadcast note to the folio this session.)

## 🛠 Friction → guard
A new cog+subsystem silently trips **8 different generated-artifact / registry-drift guards**
(hub_registry primary_children, view-base allowlist ×2 ground-truths, settings command-map doc,
dashboard.json, site.json, extension-crosswalk overlay, env-vars doc). They're individually
well-signposted but there's no single "I added a subsystem — what must I regenerate?" checklist.
*Guard shipped (docs, free-to-ship):* the design doc + folio note. *Proposed (router-worthy):* a
`scripts/new_subsystem.py`-style **post-add checklist or a `--fix-all` regen aggregator** so the
8-guard scramble becomes one command — candidate DISCUSS Q for the owner (touches tooling, not
self-edited config).

## Context delta
- **Needed but not pointed to:** the full "adding a subsystem" regen set (the 8 guards above) is
  spread across scripts/tests with no index — orientation routes to architecture/ownership but not
  to "regenerate these N artifacts". → the Friction→guard proposal.
- **Pointed to but didn't need:** CodeGraph — this was a greenfield additive build; `context_map`
  + reading the blackjack/farm patterns directly carried it.
- **Discovered by hand:** the two mirrored game-view allowlist ground-truths
  (`architecture_rules/canonical_helpers.yaml § base_view.exemptions` **and**
  `scripts/check_consistency.py _BASE_CLASS_ALLOWED_PATHS`) must both list a new game-view path;
  the parity test enforces it but nothing routes you there until it fails.
