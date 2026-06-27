# Blackjack — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `blackjack` · **Type:** game · **Family:** competitive
> **State:** ◐ assessed · **Assessed:** 2026-06-27 · **Certified:** —
> Source: `disbot/cogs/blackjack_cog.py` + `disbot/cogs/blackjack/` · `disbot/views/blackjack/` +
> `disbot/views/games/blackjack_panel.py` · `disbot/services/blackjack_engine.py` /
> `blackjack_state.py` · settings: `disbot/cogs/blackjack/schemas.py`

> **Worked pilot for the feature-completion system** ([README](../README.md)). Demonstrates the
> rubric on a near-complete unit: Blackjack is feature-rich, money-safe, and well-tested — and the
> assessment still surfaces a concrete 5-item punch-list, including one real product decision.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **All modes exist** — solo-vs-house (`blackjack_cog.py:430`), PvP (`:442`), tournament (`:515`).
- [ ] **Every standard action exists** — ✅ hit / stand / double-down (`views/blackjack/solo_view.py:154-215`);
      ❌ **split, insurance, surrender are absent** (no engine/view support). → punch-list #1.
- [x] **Loop runs start→finish** — deal→play→resolve→payout in all three modes; no dead-ends.
- [x] **No placeholder controls** — end-of-hand controls disable into a result view (`solo_view.py:271-302`).
- [x] **Rewards wired** — `economy_service` (solo) + `game_wager_workflow` (PvP/tournament).

### B. UI & buttons — "right buttons in the right places"
- [x] **Game panel exists** — Solo Free Play · Solo Bet · Challenge Player · Tournament · Status ·
      📖 Rules (`views/games/blackjack_panel.py:454-571`).
- [ ] **Every action has a control in the right place** — yes for implemented actions; **PvP bet is
      command-only** (`!bj @player [bet]`); the panel's "Challenge Player" has no bet selector. → punch-list #2.
- [x] **Rules affordance** — 📖 Rules on the panel.
- [x] **Return navigation** — "◀ Back to Blackjack" on the result view (`solo_view.py:286-302`).
- [x] **Terminal state correct** — disabled shells + result-view swap + `SettleOnceMixin` (PvP).
- [x] **Consistent copy/embeds** — house-style embeds (`views/blackjack/embeds.py`).

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — bet presets 10/25/50/100/Custom (`blackjack_panel.py:173-214`).
- [x] **Replay without retyping** — "🔁 Play again" reuses the same bet (`solo_view.py:286`).
- [ ] **Quick re-bet** — "Play again" can't adjust the bet without going back to the picker. → minor (folded into #2).
- [x] **Reachable the natural way** — `!blackjack`/`!bj` + Games hub + Help.

### D. Edge cases & lifecycle — "works as intended"
- [x] **Timeout** — solo 120s, PvP 60s, tournament configurable; disable + cleanup (`solo_view.py:134`, `pvp_view.py:89`).
- [x] **Expired interaction** — `safe_defer`/`safe_edit`/`safe_followup` guard all callbacks.
- [x] **Authority re-checked** — per-view `interaction_check` (`solo_view.py:125`, `pvp_view.py:46`).
- [x] **Concurrency / settle-once** — `SettleOnceMixin.claim_settlement` + a regression test
      (`tests/unit/views/test_blackjack_pvp_settle_once.py`).
- [x] **Restart per ADR-002** — not restart-safe by design; **money-safe** (tournament refunds
      stranded entries on recovery / guild-remove, `blackjack_cog.py:228-375`).

### E. Money-safety integration
- [x] **Audited seam** — solo via `economy_service`; PvP/tournament via `game_wager_workflow`
      (escrow-at-accept `pvp_view.py:121-137`; idempotent settle/refund/payout).
- [x] **No mint window** — stakes escrowed atomically at accept; replays no-op.
- [x] **Recovery paths** — cog_load + on_guild_remove refund/clear stranded state.

### F. Wiring & discoverability
- [x] **Registry** — key `blackjack`, `entry_points: [blackjack, bj]`, `parent_hub: games`,
      `hub_group: competitive`, caps `game.play` / `tournament.manage` (`subsystem_registry.py:718`).
- [x] **Help + Games hub** — listed under the Games hub.
- [x] **Settings** — `default_entry_fee` via the schema (`cogs/blackjack/schemas.py:46`).

### G. Tests & evidence (required for ✔)
- [x] **Loop tests** — engine + solo/PvP/tournament persistence + replay (`tests/unit/.../test_blackjack_*`).
- [ ] **Edge tests** — settle-once ✅; **tournament-timeout forfeit, guild-removal cleanup, and
      natural-blackjack auto-payout are untested** (code paths exist). → punch-list #3.
- [x] **Money tests** — escrow/settle covered via persistence + settle-once suites.
- [ ] **Live walkthrough recorded** — pending. → punch-list #4.
- [ ] **Owner ✔** — pending. → punch-list #5.

## Punch-list (clear these to certify)

1. **Product decision: split / insurance / surrender.** Implement the three standard actions, **or**
   the owner **waives** them as out-of-scope for SuperBot's blackjack (some bots deliberately omit
   them). This is the one item that needs an owner call before it can be ticked or waived.
2. **PvP bet selector in the panel** — add a bet picker to "Challenge Player" so PvP isn't
   command-only; carries the quick-rebet convenience too.
3. **Edge tests** — tournament-timeout forfeit, guild-removal cleanup, natural-blackjack payout.
4. **Live walkthrough** — `/verify-bot` boot + scripted click-through of solo / PvP / tournament,
   with screenshots, attached here.
5. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move."

## Evidence

- **Tests:** `tests/unit/services/test_blackjack_engine.py` · `tests/unit/cogs/test_blackjack_{solo,pvp,tournament}_persistence.py` ·
  `tests/unit/views/test_blackjack_solo_replay.py` · `tests/unit/views/test_blackjack_pvp_settle_once.py`
- **Walkthrough:** pending (punch-list #4)
- **Owner sign-off:** pending (punch-list #5)

## Verdict

Blackjack is **substantially complete and production-safe** — all three modes, full money-safety,
strong lifecycle handling, good test coverage. It is **not yet `✔ certified`**: it needs the owner's
split/insurance/surrender call (#1), the PvP-panel bet selector (#2), three edge tests (#3), and the
recorded walkthrough + sign-off (#4, #5). A focused session clears #2–#4; #1 and #5 are owner calls.
