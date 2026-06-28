# Casino (multiplayer poker) — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `casino` · **Type:** game · **Family:** competitive
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/casino_cog.py` · `disbot/views/casino/` (`hub.py` · `poker_table.py`) ·
> `disbot/utils/poker/` (`engine.py` · `evaluate.py`) · `disbot/utils/cards/__init__.py` ·
> registry `disbot/utils/subsystem_registry.py:742` (`casino`).
> Design: [`../../casino-poker-design-2026-06-22.md`](../../casino-poker-design-2026-06-22.md).

> Assessed during the completion-first deepening run (Q-0209), grounded in a code read (evidence
> spot-verified against source). Casino poker is a **full, self-contained Texas Hold'em** built on a
> novel per-player **ephemeral broadcast** frame (each seat sees its own hole cards in a private
> message that re-renders on every state change). The engine (side pots, all-in run-out, showdown) is
> pure and well-tested. It is **money-safe by exclusion** — v1 uses table **play-chips**, never the
> real economy. The punch-list below is UX-depth + the one terminal-nav gap; all owner-paced.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes exist + reachable** — Texas Hold'em (v1 scope); roulette is an explicit disabled
      placeholder on the hub (`hub.py:102-115`). Per-player ephemeral hands are the marquee feature
      (`poker_table.py:406-456`).
- [~] **Every standard action exists** — fold / check / call / raise(min) / raise(pot) / all-in all
      present (`PokerSeatView`, `poker_table.py:712-778`). *Missing vs best-in-class:* a **custom
      raise amount** (only min/pot/all-in presets, no enter-amount modal) and **rebuy** after bust
      (busted seats sit out, `engine.py` `begin_hand` skips `stack <= 0`). Both are deliberate v1
      simplifications — listed, not silently absent (punch-list #2/#3).
- [x] **Loop runs start→finish** — lobby join → deal+blinds (`engine.py:173-239`) → preflop/flop/turn/
      river betting (`engine.py:319-439`) → showdown best-hand settle (`engine.py:463-513`) → "Deal
      next hand" (`poker_table.py:243-271`). All-in run-out + **multi-way side pots** are handled
      (`engine.py:444-496`) and tested.
- [~] **No dead-end/placeholder controls** — in-game and lobby controls are correct, **but** the
      **closed-table teardown drops all views** (`poker_table.py:388-397`: the public message and every
      seat panel are edited to `view=None`) with no Back-to-Casino affordance, and a timed-out lobby
      leaves disabled buttons (the standard `BaseView.on_timeout` disable). The table is intentionally
      terminal per ADR-002, and the Casino hub is re-reachable via `!casino`, so this is a **minor UX
      gap**, not a crash — but it is the textbook dead-end the `no_dead_end` guard targets (the guard
      doesn't flag it because the teardown lives on the `PokerTable` *manager*, not a `View.stop()`
      handler). Punch-list #1.
- [x] **Rewards wired** — **play-chips only**, no `economy_service` / `game_wager_workflow` import in
      `engine.py` (verified: imports are `utils.cards` + `utils.poker.evaluate` + stdlib only). Chips are
      synthetic, conserved across betting/showdown (`test_poker_engine.py`). No game-XP on table finish
      yet (follow-up).

### B. UI & buttons — "right buttons in the right places"
- [x] **Game panel exists** — `CasinoHubView` (`hub.py:50-116`), `SUBSYSTEM = "casino"`, extends
      `HubView` → standard nav (Help + ↩ Games). "New Poker Table" launches a table; roulette disabled.
- [x] **Every action has a control** — all 13 actions on buttons (join/leave/start/close on the lobby
      view; fold/check/call/raise×3 on the per-seat ephemeral; deal-next/end-table on the end view).
      Nothing buried; raise amounts pre-computed so no modal round-trip.
- [~] **Rules / how-to affordance** — discoverable via Help hook (`casino_cog.py:67-72`) and the design
      doc, but **no in-panel "📖 Rules" button** on `CasinoHubView` (RPS has one). Punch-list #4.
- [~] **Return navigation everywhere** — the **hub** carries standard nav, but a launched **table's**
      public + seat messages carry **no ↩ Casino** button (`poker_table.py`), and the closed table has
      none (see A). Mid-table the only nav is gameplay actions. Punch-list #1.
- [x] **Terminal state visually correct** — finished hands swap to the end view (Deal next / End
      table); on timeout controls disable. No stale clickable game buttons.
- [x] **Embeds/copy consistent** — house style; no debug/placeholder strings (roulette is a labeled
      "coming later", not a broken button).

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — join = 1 click, host start = 1 click, deal-next = 1 click; raise presets
      avoid typing.
- [x] **Replay without retyping** — "Deal next hand" on the end view (`poker_table.py:633-643`) replays
      with the same table; no command re-issue.
- [x] **Sensible defaults + presets** — 1000 start stack, 5/10 blinds, 8 seats, 90 s turn timeout
      (`poker_table.py:48-55`); raise presets (min/pot/all-in).
- [x] **Reachable the natural way** — `!casino` / `!poker` / `!holdem` (registry `entry_points`,
      verified) **and** the Games hub (`parent_hub: games`, `hub_group: competitive`) **and** the Help
      hook all lead to it.

### D. Edge cases & lifecycle — "works as intended"
- [x] **Timeout** — lobby (600 s) and game (1800 s) views disable on timeout; **turn timeout (90 s)
      auto-checks-or-folds** the AFK player (`poker_table.py:329-348`) so a table never stalls.
- [x] **Expired / stale interaction** — `safe_defer` on the non-immediate callbacks; broadcast edits
      wrapped in `try/except discord.HTTPException`; seat webhook token refreshed from each live
      interaction (`poker_table.py:296-299`).
- [x] **Authority re-checked** — host-only gate on start/cancel/deal-next/end (`interaction.user.id ==
      host.id`); per-seat `interaction_check` pins each player to their own panel
      (`poker_table.py:698-705`).
- [x] **Concurrency / settle-once** — one table per channel (`_tables` dict); a **turn-token** guard
      blocks stale timeouts from firing (`poker_table.py:317-349`). No DB rows → no multi-settle window.
- [x] **Restart per ADR-002** — in-memory table state, **not** restart-safe by design (footer says so);
      **money-safe trivially** — no real coins are ever staked, so a restart strands nothing of value.

### E. Money-safety integration
- [x] **No real-money seam to audit (by design)** — v1 is play-chips only; `engine.py:7-12` documents
      that real-coin buy-ins would need N-party escrow through `game_wager_workflow` as a follow-up.
      **Risk: zero** today.
- [x] **No mint window** — chips never leave a wallet (there is none); per-hand chip conservation is
      test-pinned (`test_poker_engine.py` chips-conserved cases).
- [x] **Recovery paths** — n/a for value (play-chips); a bot restart simply ends the table.
- [ ] **Gate before any real-coin variant ships** — buy-in MUST route per-player through
      `game_wager_workflow` (N-party escrow), wrap commits in a DB transaction, make settle/refund
      idempotent, and add the crash/guild-removal refund path. Recorded so the follow-up can't skip it.

### F. Wiring & discoverability
- [x] **Registry entry** — `casino` (`subsystem_registry.py:742`), tier `user`, capability
      `casino.game.play`, related `blackjack`.
- [x] **Command + hub + Help** — all three resolve (see C); aliases pinned by `test_casino.py`.

## Punch-list (gaps — all owner-paced)

1. **Terminal-nav gap (UX):** a closed table (`End table`) and a timed-out lobby drop their views with
   no ↩ Casino / Help affordance (`poker_table.py:388-397`). Adding nav to a torn-down multi-player
   ephemeral broadcast is non-trivial (webhook tokens, N seat messages), so it's owner-paced, not a
   safe drive-by. *(Not flagged by `no_dead_end` — the teardown is on the `PokerTable` manager, not a
   `View.stop()` handler.)*
2. **No custom raise amount** — only min/pot/all-in presets; a best-in-class table offers an
   enter-amount option. Deliberate v1 UI simplification.
3. **No rebuy / chip reload** — busted seats sit out; no second buy-in. Deliberate (keeps v1 simple).
4. **No in-panel "📖 Rules" button** on `CasinoHubView` — rules reach only via Help; RPS sets the
   precedent of a panel Rules affordance.
5. **No hand history / per-player stats / game-XP** — no win-rate leaderboard or XP on table finish.
   Follow-up depth.
6. **No bot opponents** — can't solo-practice or fill empty seats.
7. **Real-coin follow-up** — see E (the escrow/idempotency/refund gate to honor before any wagered
   variant).

## Path to ✔ certified

`◐ → ✔` needs: punch-list #1 + #4 addressed (or owner-waived), a recorded **live walkthrough**
(verify-bot boot → multi-account table → a full hand to showdown + a closed table, with screenshots),
green engine/edge tests (already 26 across `test_poker_engine` / `test_poker_evaluate` / `test_casino`),
and the **owner ✔**. The remaining punch-list items are explicit v1 scope reductions that can be
waived-with-reason at certification.
