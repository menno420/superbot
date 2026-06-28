# Rock Paper Scissors / tournament — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `rps_tournament` · **Type:** game · **Family:** competitive
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/rps_tournament_cog.py` + `disbot/cogs/rps_tournament/` (`_quickplay` ·
> `_bot_matches` · `_persistence` · `rules` · `_stage` · `schemas`) · `disbot/views/rps/`
> (`solo_play` · `pvp_challenge` · `pvp_play` · `move_picker` · `registration`) +
> `disbot/views/games/rps_panel.py` · `disbot/services/game_wager_workflow.py`

> Assessed during the completion-first deepening run (Q-0209). RPS is one of the most *mode-complete*
> games in the bot — four rule sets, four flows (solo-vs-bot, PvP, bot-batch, full tournament bracket),
> atomic escrow money-safety, and strong persistence/recovery. The assessment surfaces a small
> punch-list whose **help-text drift is fixed in this PR**; the rest is owner-paced.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes exist + reachable** — solo-vs-bot quickplay + PvP (`rps_tournament_cog.py:770`,
      `_quickplay`), bot-batch matches (`:409`, `_bot_matches`), full tournament bracket
      (register → start → per-match channels, `:197`/`:366`). Four rule modes (classic / lizard_spock /
      chess / elemental, `rules.py:37`).
- [x] **Every standard action exists** — pick move, bet, challenge, rematch (solo), bracket advance;
      benchmarked against best-in-class RPS bots, nothing standard is missing.
- [x] **Loop runs start→finish** — solo `_play`→resolve→result view; PvP escrow-at-accept→both-pick→
      atomic resolve; tournament seed→match channels→resolve+advance→idempotent payout.
- [x] **No dead-end/placeholder controls** — solo + bet + challenge-select + tournament sub-views all
      swap to terminal/result states; the PvP-play result now carries ◀ Back to RPS too (fixed this PR,
      punch-list #2).
- [x] **Rewards wired** — solo win via `economy_service`; PvP/tournament via `game_wager_workflow`
      (`pvp_challenge.py:77`, `pvp_play.py:177`, `rps_tournament_cog.py:673`); stats via `rps_players`.

### B. UI & buttons — "right buttons in the right places"
- [x] **Game panel exists** — `RPSPanelView` (▶ Quick Play · 💰 Bet Match · 👤 Challenge Player ·
      🏆 Tournament · 📖 Rules), `SUBSYSTEM = "rps_tournament"` (`rps_panel.py:557`).
- [x] **Every action has a control** — quick play / bet / challenge / tournament on the panel; presets
      on the bet sub-view; move picker ephemeral. PvP is reachable from the panel (not command-only).
- [x] **Rules affordance** — 📖 Rules on the panel (`build_rps_rules_embed`, `rps_panel.py:157`).
      ✅ **fixed (punch-list #3, this PR):** the rules embed now carries a "Timeouts & forfeits" field.
- [x] **Return navigation everywhere** — ✅ for panel-spawned sub-views (solo result, bet preset,
      challenge select, tournament sub-view all carry **◀ Back to RPS**). ✅ **fixed (punch-list #2,
      this PR):** the **PvP play** result is now posted with `_RpsPvpResultView` carrying ◀ Back to RPS
      (`pvp_play.py`), so a resolved PvP match is no longer a bare dead-end embed.
- [x] **Terminal state correct** — solo/challenge/tournament views disable controls on terminal;
      `SettleOnceMixin` guards PvP resolution.
- [x] **Consistent copy/embeds** — house-style; no debug/placeholder strings.

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — Quick Play is one click; Bet Match offers 10/25/50/100 + Custom presets.
- [x] **Replay without retyping** — 🔁 Play again on the solo result view (`solo_play.py:174`). *(PvP has
      no rematch button — owner-paced, punch-list #5.)*
- [x] **Sensible defaults + presets** — bet presets; mode/best-of defaults with admin override.
- [x] **Reachable the natural way** — `!rps` + the Games hub + Help (3 aliases resolve, pinned by
      `test_rps_naming.py`).

### D. Edge cases & lifecycle — "works as intended"
- [x] **Timeout** — solo/result/challenge/play all disable on timeout; PvP play forfeits a non-picker
      (`pvp_play.py:210`); move picker 55 s.
- [x] **Expired / stale interaction** — `safe_defer`/`safe_edit` across callbacks.
- [x] **Authority re-checked** — `interaction_check` on solo / challenge / play / result views; admin
      gate on tournament-control buttons.
- [x] **Concurrency / settle-once** — PvP play uses `SettleOnceMixin`; tournament resolve gates on
      both-moves-ready + atomic win increment.
- [x] **Restart per ADR-002** — not restart-safe by design; **money-safe** — entry fees and PvP escrow
      recover/refund on `cog_load` + `on_guild_remove` (`rps_tournament_cog.py:147-191`).

### E. Money-safety integration
- [x] **Audited seam** — all wagers route through `game_wager_workflow` (escrow-at-accept, idempotent
      settle/refund/payout); reason strings consistent.
- [x] **No mint window** — PvP stakes escrowed atomically at accept; solo never pre-debits.
- [x] **Recovery paths** — `recover_escrow` / `recover_rps_pvp_pending` / `recover_rps_tournament`.

### F. Wiring & discoverability
- [x] **Registry** — key `rps_tournament`, `entry_points: [rps]`, `parent_hub: games`,
      `hub_group: competitive`, caps `game.join` / `tournament.manage`
      (`subsystem_registry.py:853`).
- [x] **Help + Games hub** — `build_help_menu_view` returns the panel; discovered once under Games.
- [x] **Settings** — `default_entry_fee` schema (`schemas.py:33`); `default_mode`/`default_best_of`
      via `!rpssettings`.

### G. Tests & evidence (required for ✔)
- [x] **Loop tests** — persistence/recovery, solo replay, panel actionability, naming/Help routing
      (`test_rps_tournament_persistence.py`, `test_rps_solo_replay.py`, `test_rps_naming.py`,
      `test_help_actionability_contract.py`).
- [~] **Edge tests** — ✅ **partly closed (punch-list #4, this PR):**
      `tests/unit/cogs/test_rps_pvp_deadend.py` pins the PvP `_resolve` posting the nav-bearing result
      view, the result-view authority, and a `!rpshelp` output drift-guard. Still open: a dedicated
      bot-batch match test.
- [x] **Money tests** — escrow/settle/refund via the persistence suites.
- [ ] **Live walkthrough recorded** — pending. → punch-list #6.
- [ ] **Owner ✔** — pending. → punch-list #7.

## Punch-list (clear these to certify)

1. ~~**`!rpshelp` text drift (every command misnamed).**~~ ✅ **FIXED 2026-06-28 (this PR).** The
   `rps_help` text listed underscored commands that don't exist (`!rps_register`, `!rps_start`,
   `!rps_bot`, `!rps_settings`, `!rps_help`) plus a **`!rps_leaderboard` command that was never
   implemented**. Rewritten to the real no-underscore names (`!rpsregister`/`!rpsstart`/`!rpsbot`/
   `!rpssettings`/`!rpshelp`) led by `!rps` (the panel), with the bogus leaderboard line removed.
2. ~~**PvP play result has no back affordance.**~~ ✅ **FIXED (this PR).** `_resolve` now posts the
   result with `_RpsPvpResultView` carrying **◀ Back to RPS** (the shared `_make_rps_back_button`
   pattern the solo/bet/challenge views use); either participant may use it.
3. ~~**Rules embed completeness.**~~ ✅ **FIXED (this PR)** — `build_rps_rules_embed` gained a
   "Timeouts & forfeits" field (forfeit on no-pick → opponent takes the pot; both no-pick → refund).
4. **Edge tests** — ✅ **partly closed (this PR):** PvP `_resolve` result-view + authority pins and a
   `!rpshelp` output drift-guard (`test_rps_pvp_deadend.py`). Still open: a dedicated bot-batch match
   test.
5. **PvP rematch affordance** *(owner)* — a 🔁 Rematch button on the PvP result (mirrors the solo
   result), if one-off PvP isn't the intended design.
6. **Live walkthrough** — `/verify-bot` boot + scripted click-through (quick play → bet → challenge →
   tournament register/start), with screenshots.
7. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move."

## Evidence
- **Tests:** `tests/unit/.../test_rps_tournament_persistence.py` · `test_rps_pvp_pending_persistence.py` ·
  `test_rps_solo_replay.py` · `test_rps_naming.py` · `test_rps_guild_scope.py` ·
  `test_help_actionability_contract.py` · **`test_rps_pvp_deadend.py` (PvP result back-affordance +
  rpshelp drift-guard — this PR)**
- **Walkthrough:** pending (punch-list #6)
- **Owner sign-off:** pending (punch-list #7)

## Verdict
RPS is **substantially complete and money-safe** — the most mode-rich game in the bot (four rule sets,
four flows), with atomic escrow, full persistence/recovery, and good panel UX. The offline gaps are now
cleared: the `!rpshelp` drift (#1), the PvP-play back affordance (#2), the rules copy (#3), and most of
the edge tests (#4) are **fixed across this PR + the prior one**. It is **not yet `✔ certified`**: what
remains is owner-paced / live-bot — an owner PvP-rematch call (#5), a bot-batch match test (tail of #4),
and the recorded walkthrough + sign-off (#6/#7). Code-side, this unit is now close to ✔-ready.
