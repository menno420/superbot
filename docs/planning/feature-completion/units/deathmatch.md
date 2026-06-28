# Deathmatch — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `deathmatch` · **Type:** game · **Family:** competitive
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/deathmatch_cog.py` + `disbot/cogs/deathmatch/` (`actions` · `schemas`) ·
> `disbot/views/games/deathmatch_panel.py` (panel + bot-duel views) · `disbot/utils/db/games/deathmatch.py` ·
> gear seam: `disbot/utils/equipment.py` + `disbot/services/mining_workflow.py` (wear)

> Assessed during the completion-first deepening run (Q-0209). Deathmatch is a gear-aware 1v1 duel —
> PvP (human) + a Fight-Bot mode — with clean settle-once handling on the bot path and good test
> coverage there. The assessment's **headline gap is a real one**: the **PvP** terminal views are
> dead-ends (no return navigation after a duel finishes), even though the **bot-duel** path does it
> correctly. That, plus a missing PvP rematch + PvP loop tests, is the path to certification.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes exist + reachable** — PvP 1v1 (`!deathmatch @user` / 👤 Challenge Player) and **Fight Bot**
      (🤖, `deathmatch_panel.py:511`); both reachable from the panel. (No FFA/solo-no-reward by concept;
      see punch-list #6 owner note.)
- [x] **Every standard action exists** — Attack / Defend, gear-modified HP/damage/defense, bot AI
      (`deathmatch/actions.py:40`), crit, armor floor.
- [x] **Loop runs start→finish** — challenge→accept→turn loop→resolve→leaderboard (PvP,
      `deathmatch_cog.py:214`); gear-load→duel→result view (bot, `deathmatch_panel.py:216`).
- [ ] **No dead-end controls** — ❌ **the PvP `_DuelView` and `_ChallengeView` are trapped** (see B,
      punch-list #1). The bot-duel path is clean (swaps to `_BotDuelResultView`).
- [x] **Rewards wired** — leaderboard W/L via `db.update_deathmatch`; gear wear ticked once per PvP duel
      via `mining_workflow.wear_tick` (`deathmatch_cog.py:68`). Free game (no coins/XP by design).

### B. UI & buttons — "right buttons in the right places"
- [x] **Game panel exists** — `DeathmatchPanelView(HubView, SUBSYSTEM="deathmatch")` (🤖 Fight Bot ·
      👤 Challenge Player · 📖 Rules), Help hook + Games hub.
- [x] **Every action has a control** — Fight Bot / Challenge / Rules on the panel; Attack/Defend in the
      duel; opponent picker on Challenge.
- [x] **Rules affordance** — 📖 Rules on the panel (`deathmatch_panel.py:67`).
- [ ] **Return navigation everywhere** — ❌ **headline gap.** `_BotDuelResultView` declares
      `SUBSYSTEM = "deathmatch"` so `attach_standard_nav` gives it 📚 Help + ↩ Games (correct). But the
      **PvP** `_DuelView` (in-game) and `_ChallengeView` (accept prompt) are plain `discord.ui.View`
      subclasses (`deathmatch_cog.py:94,252`): on finish / timeout / decline they disable their buttons
      and **stop with no back affordance** → the player is stranded on a dead embed. The 2026-06-23
      "finished duel is never a dead-end" directive was applied to the bot path and **missed for PvP**.
      → punch-list #1.
- [x] **Terminal state correct** — controls disable on terminal in every branch (bot path additionally
      swaps to the result view); `SettleOnceMixin` on the bot duel.
- [x] **Consistent copy/embeds** — house-style; no debug/placeholder strings found.

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — Challenge opens the opponent picker directly; Fight Bot launches at once.
- [ ] **Replay without retyping** — ✅ 🔁 Play again on the **bot** result view (`deathmatch_panel.py:354`);
      ❌ **no PvP rematch** — after a PvP duel the player must re-issue `!deathmatch @opponent`. → folded
      into punch-list #1 (the PvP result view should carry a rematch).
- [x] **Sensible defaults** — turn timeout is per-guild configurable (`schemas.py`).
- [x] **Reachable the natural way** — `!deathmatch`/`!dm` + Games hub + Help.

### D. Edge cases & lifecycle — "works as intended"
- [x] **Timeout** — challenge 30 s (guarded by `_resolved`), turn 60 s (configurable), bot duel 120 s.
- [x] **Expired / stale interaction** — `safe_*` guards; `_resolved` flag stops a stale challenge
      timeout from clobbering an accepted duel (BUG-0013 regression test).
- [x] **Authority re-checked** — `interaction_check` pins the current-turn player (PvP), the challenged
      opponent (challenge), and the starting player (bot duel).
- [x] **Concurrency / settle-once** — bot duel uses `SettleOnceMixin.claim_settlement`; PvP uses a
      `_resolved`/`is_over` guard (equivalent, though less uniform than the mixin).
- [x] **Restart per ADR-002** — in-memory duel state, not restart-safe (accepted); **no money at stake**
      (free game); duel-key + active-duel tracking prevent double-join.

### E. Money-safety integration
- [x] **No wagering** — Deathmatch is free by design; no `game_wager_workflow` flow, no mint window.
      (`related_subsystems: ["economy", ...]` is a soft relation, not a coin dependency.) Optional
      coin-staking is an owner-paced future call (punch-list #5).

### F. Wiring & discoverability
- [x] **Registry** — key `deathmatch`, `entry_points: [deathmatch, dm]`, `parent_hub: games`,
      `hub_group: competitive`, caps `game.challenge` / `stat.view` (`subsystem_registry.py:829`).
- [x] **Help + Games hub** — `build_help_menu_view` returns the panel; in Games `primary_children`.
- [x] **Settings** — `turn_timeout` schema, read at accept (`deathmatch_cog.py:325`).

### G. Tests & evidence (required for ✔)
- [x] **Loop tests (bot path)** — bot AI, combat stats, gear wear, guild scope, settle-once
      (`test_deathmatch_bot_duel.py`, `test_deathmatch_combat_stats.py`, `test_deathmatch_gear_wear.py`,
      `test_deathmatch_guild_scope.py`).
- [ ] **Edge tests (PvP path)** — the PvP `_DuelView` finish/timeout/settle is untested (only the bot
      path is). → punch-list #3.
- [x] **Money tests** — n/a (free game).
- [ ] **Live walkthrough recorded** — pending. → punch-list #4.
- [ ] **Owner ✔** — pending. → punch-list #5/#6.

## Punch-list (clear these to certify)

1. **PvP terminal views are dead-ends (headline).** `_DuelView` and `_ChallengeView`
   (`deathmatch_cog.py:94,252`) are plain `discord.ui.View`s; on finish/timeout/decline the player has
   no back affordance. **Fix (turn-key, mirrors the bot path):** swap each to a small
   `HubView`-derived result view (`SUBSYSTEM = "deathmatch"`, so `attach_standard_nav` adds 📚 Help +
   ↩ Games) on terminal, carrying a **🔁 Rematch** button — closing both the dead-end (rubric B) **and**
   the missing-PvP-rematch convenience (rubric C) in one change. Owner directive precedent: the
   2026-06-23 "never a dead-end" rule (already applied to `_BotDuelResultView`).
2. **Uniformity (optional):** move the PvP `_resolved`/`is_over` guard onto `SettleOnceMixin` so PvP and
   bot paths share one settle-once primitive.
3. **PvP loop tests** — add finish/timeout/settle-once pins for the PvP duel (mirror the bot-duel tests),
   including correct `guild_id` on a timeout-recorded result.
4. **Live walkthrough** — `/verify-bot` boot + scripted click-through (challenge → accept → duel →
   finish → rematch; Fight Bot → result → play again), with screenshots.
5. **Coin-staking** *(owner)* — decide whether PvP gains optional wagering via `game_wager_workflow`
   (Blackjack/RPS have it) or stays a free game.
6. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move."

## Evidence
- **Tests:** `tests/unit/.../test_deathmatch_bot_duel.py` · `test_deathmatch_challenge_timeout.py` ·
  `test_deathmatch_combat_stats.py` · `test_deathmatch_gear_wear.py` · `test_deathmatch_guild_scope.py`
- **Walkthrough:** pending (punch-list #4)
- **Owner sign-off:** pending (punch-list #6)

## Verdict
Deathmatch is **feature-rich and money-safe** (no stakes), with gear integration, two modes, and a
well-tested, dead-end-free **bot** path. It is **not yet `✔ certified`**: the **PvP** path has a real
trapped-view dead-end (#1, the headline) that also carries the missing PvP rematch, plus PvP loop tests
(#3) and the owner walkthrough/sign-off (#4/#6). #1 is a contained, turn-key fix that mirrors the
already-shipped bot-duel result view — a strong next slice for a focused follow-up.
