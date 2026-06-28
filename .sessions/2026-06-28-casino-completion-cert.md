# 2026-06-28 — Casino (poker) feature-completion certificate (Q-0209)

> **Status:** `complete`

**Run type:** routine · dispatch

## What I'm about to do

Second slice of this dispatch run (slice 1 = the no_dead_end arch guard, #1529, merged). The S1
completion-first arc (Q-0209) names assessing the remaining unassessed games. I assessed **Casino
multiplayer poker** against the game rubric — grounded in a code read (evidence spot-verified against
source: registry key, no-economy imports = play-chips, closed-table `view=None` teardown, 26 tests).

**The slice (docs only):** a `◐ assessed` certificate `units/casino_poker.md` with the full A–F rubric
filled in + a punch-list (the one terminal-nav gap + best-in-class depth gaps, all owner-paced), and
the completion ledger updated (Casino → assessed, scoreboard regenerated 7→8 assessed).

Offline / self-mergeable on green.

## What shipped (PR #1530)

A `◐ assessed` **feature-completion certificate** for the **Casino (multiplayer poker)** unit —
`docs/planning/feature-completion/units/casino_poker.md` — the full A–F game rubric filled in,
grounded in a code read and **spot-verified against source** (Q-0120: cross-agent evidence verified,
not trusted):

- **Registry** `casino` (`subsystem_registry.py:742`), commands `!casino`/`!poker`/`!holdem`.
- **A. Loop** — complete Texas Hold'em (join → deal/blinds → preflop–river → showdown → next hand);
  multi-way **side pots** + all-in run-out tested (`utils/poker/engine.py`).
- **E. Money-safety** — **play-chips only**, verified: `engine.py` imports `utils.cards` +
  `utils.poker.evaluate` + stdlib, **no** `economy_service`/`game_wager_workflow`. Risk = zero today.
- **Punch-list (all owner-paced):** #1 the closed-table/timed-out-lobby **terminal-nav gap**
  (`poker_table.py:388-397`, `view=None` teardown — minor UX, not a `no_dead_end` hit because the
  teardown is on the `PokerTable` *manager*, not a `View.stop()` handler); #2–6 v1 depth (custom raise,
  rebuy, in-panel Rules button, hand-history/XP, bot opponents); #7 the real-coin escrow gate.
- **Ledger** updated (Casino → assessed), scoreboard regenerated **7 → 8 assessed** (`--check` clean).
- S1 ▶ Next de-staled (8/36; Casino removed from the unassessed list).

Docs only; CI = `check_docs --strict` + `check_consistency` + scoreboard `--check` green (the full
pytest runs in CI but no runtime code changed). Self-merged on green.

## 📤 Run report

- **Did:** assessed the Casino (poker) unit against the game rubric → a `◐ assessed` completion
  certificate + ledger update (slice 2 of this dispatch run) · **Outcome:** shipped
- **Shipped:** #1530 — `units/casino_poker.md` + ledger/scoreboard + S1 de-stale.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none (the punch-list is informational; `◐ → ✔` needs an owner
  live-walkthrough sign-off, which is the standing Q-0209 gate, not a new decision).
- **⚑ Owner manual steps:** none (docs only).
- **⚑ Self-initiated:** yes — empty-fire dispatch; the named S1 ▶ Next "assess more units" item
  (grounded in the live queue + Q-0209) → built without a dispatch/owner ask (Q-0172).
- **↪ Next:** S1 ▶ Next offline = assess the remaining unassessed games (**Mining** [big read],
  **Creatures**), one cert each, then the server-fn units; or the next fishing offline craft successor.

## ⟲ Run note (slice 2 of 2)

This was the second slice of a single dispatch run; slice 1 (#1529, the `no_dead_end` guard) and slice 2
(#1530, this cert) are complementary — the guard now *enforces* the dead-end rubric line that this cert
*manually checked* for Casino, and the cert even documents why the guard doesn't fire on Casino's one
gap (manager-level teardown, not a `View.stop()` handler). The full Q-0089/Q-0102/Q-0104 enders live on
slice 1's card (`2026-06-28-no-dead-end-view-guard.md`) to avoid duplication across the two cards of one run.
