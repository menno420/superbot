# 2026-06-30 — BTD6 boss-fight estimator (estimate, don't refuse)

> **Status:** `complete`
<!-- born-red flow (Q-0133): `in-progress` while open; flipped to `complete` as the final close step. -->

**PR:** [#1574](https://github.com/menno420/superbot/pull/1574) — BTD6 boss-fight estimator.
**Branch:** `claude/ai-answer-storage-plan-3fvdit` (restarted from main; PR #1572 merged).
**Run type:** manual (owner-directed).

## What this run did

The owner, reviewing the review-log export, pointed out (correctly) that the bot **refuses
questions it has the data to estimate** — boss fights, "cheapest cost", "how long". It has boss
HP/speed, per-crosspath combat stats, and tower costs; the only true gap is track length. Owner
picked **the full estimator**, accepting *an estimate with stated assumptions over a refusal*.

**Design principle:** the arithmetic is **deterministic** (a compute service), not the model
doing mental math — the fix for the confabulation class seen in the #1572 export.

## Shipped (PR #1574)

- **PR1 — `services/btd6_estimator_service.py`** (the deterministic core): effective single-target
  boss DPS (via the existing `btd6_stats_service.attack_breakdown`, with an **instakill-sentinel
  filter** — the Druid 9,999,999 Vine was inflating DPS to millions), cost-to-crosspath,
  time-to-kill = HP ÷ DPS, damage-type immunity blocking, a cheapest-counters (DPS-per-dollar)
  ranking, a free-form query parser, and plain-text formatters. Every estimate carries explicit
  assumptions. **15 unit tests** against the real dump.
- **PR2 — the unified `/btd6 estimate` (+ `!btd6 estimate`) command**: `_builders.build_estimate_embed`
  + the slash/prefix twins in `_unified`. `<tower> vs <boss> [tier]` for a single estimate,
  `counters <boss>` for the ranking. Updated the unified-tree flat-lookup pin; regenerated artifacts.

Full CI mirror green (13,231 passed); `check_architecture --mode strict` 0 errors.

## Decisions made alone (owner should be aware)

- **Deferred the conversational AI-answer-path integration** (a deterministic estimate reply on
  the BTD6 answer path) to its own PR. Mis-firing a canned reply on the **gated** answer path needs
  live verification (no provider key here) — the exact risk the AI gate guards. The command is the
  offline-verifiable surface; the AI hook is the next focused, live-tested slice.
- **Did NOT fabricate track-length data.** `maps.json` has no track length and it isn't reliably
  published; inventing numbers would be worse than the honest gap. The estimator nails the
  practically-useful question (HP ÷ DPS = kill time/cost); "how long to physically cross" stays a
  documented data gap.
- **v1 is base single-target DPS** — excludes MOAB/boss bonus damage (`damageToBad`, paragon
  `boss_multiplier`), abilities, and buffs, so kill-times read high for ability/bonus-reliant
  towers. Stated in every estimate's assumptions; a "boss-aware DPS" refinement is the obvious next.

## Flagged for maintainer (try it / weak points)

- **Try it after deploy:** `!btd6 estimate super monkey 0-4-0 vs bloonarius t5` and
  `!btd6 estimate counters bloonarius t5`. The numbers are conservative base-DPS (high kill-times);
  the *relative* ranking is the useful part until the boss-aware-DPS refinement lands.
- **The conversational fix (the export's entries 3–6) is NOT in yet** — that's the deferred AI-path
  PR. This session makes the capability exist + usable; wiring it into free chat is next + needs
  your live test.

## 💡 Session idea (Q-0089)

[`compute-dont-refuse-capability-sweep-2026-06-30.md`](../docs/ideas/compute-dont-refuse-capability-sweep-2026-06-30.md)
— generalize the lesson: mine the `ai_review_log` for refusals that are actually **computable** (the
bot has the data, it just refused/confabulated — economy projections, XP-to-level, mining math) and
build a deterministic compute tool per recurring class. Adds a `computable` triage disposition.

## ⟲ Previous-session review (Q-0102)

Previous = the DDT-confabulation corpus capture (#1572). **Did well:** honest triage that resisted
"fixing" the bot's *correct* refusals, and captured the finding + vetted answer durably. **Missed /
improvement:** it framed the AI-path fix narrowly as "an owner preset" and didn't spot the bigger
pattern the owner then named — the bot refuses **computable** questions, not just confabulates. The
system improvement is exactly the Q-0089 idea: the triage script should flag *computable refusal* as
its own disposition (distinct from "data gap"), turning the review log into a compute-tool backlog.
The loop worked — the owner's nudge plus the log surfaced a whole capability class.

## 🛠 Friction → guard

- **Friction:** the **add-a-BTD6-command ripple** — a new command must add `_unified` slash+prefix
  twins + a `_builders` builder + update the unified-tree flat-lookup pin + pass the parity +
  reachability guards + regenerate artifacts. I first wrote a bare top-level command and hit those
  guards one full-suite run at a time. **Guard status:** the guards *worked* (they caught the
  wrong shape); the residual friction is discovery-at-full-suite-time. **Shipped now (free lane):**
  this log's ripple enumeration above is the durable checklist; the artifact half is already caught
  pre-push by last session's freshness guard. A `check_btd6_command_ripple` checker would be the
  "enforce" upgrade but is optional (the existing pins already enforce, just slower) — not building
  speculative tooling.

## ⚑ Self-initiated

Owner-directed feature (the owner named the goal + picked "full estimator" via AskUserQuestion). The
**scope decisions** (defer the AI-path + track-time, ship service + command) are my judgment calls,
flagged above for ratification — not unprompted idea→plan promotions.

## Doc audit (Q-0104)

`check_quality --check-only` green (docs reachable, artifacts fresh); `check_current_state_ledger
--strict` exit 0; `check_architecture --mode strict` 0 errors. Idea filed + indexed. No new owner
*rules* / router changes. Did not touch `current-state.md` Recently-shipped (merged-PRs-only).
