# Counting — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `counting` · **Type:** game · **Family:** activity
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/counting_cog.py` + `disbot/cogs/counting/` (`parsing.py` ·
> `game_logic.py` · `handler.py` · `_channel_manager.py` · `_stage.py`) ·
> `disbot/views/counting/hub_panel.py` · state: `db.get/set_counting_state`

> Assessed during the post-#1513 completion-first deepening run. Counting is a genuinely deep,
> well-engineered counting game (11 modes, DB-persisted, scope-locked, hardened by BUG-0012) — but it
> has two real player-facing completeness gaps: a **leaderboard that is tracked but never shown**, and
> **no player-facing discovery surface** (its only registered entry point is admin-only).

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes exist** — 11: normal · reverse · skip · random · multiples · prime · fibonacci ·
      squares · cubes · factorials · custom (`counting_cog.py:209-221`); math-expression parsing
      (`cogs/counting/parsing.py`). Far beyond a typical counting bot.
- [x] **The core loop runs** — post the next number → `handler.compute_decision` validates against
      `game_logic.calculate_expected_count` → mutate/persist → `apply_decision` reacts/deletes
      (`counting_cog.py:689-731`). Wrong-count handling + optional reset-on-wrong.
- [x] **No dead-end controls** — the admin `_CountingHubView` buttons drive real channel management.
- [ ] **Rewards/XP wired** — ❌ counting awards **no game_xp and no coins**; the only "reward" is a
      per-channel `leaderboard` tally (`handler.py:167-169`). The tally is now **displayed** (✅ #2
      fixed this run), but whether counting should grant XP/coins remains an owner call. → punch-list
      #1 (decision).
- [x] **Taking-turns + reset-on-wrong** options exist (`counting_cog.py:486-514,648-683`).

### B. UI & buttons — "right buttons in the right places"
- [~] **Panel exists** — an **admin** hub (`_CountingHubView`, `!countingmenu`/`!cm`) for channel
      setup; counting is *played by posting numbers in a channel*, so a player "game panel" is less
      essential — but discovery/rules for players is thin (see F).
- [x] **Leaderboard is now visible (✅ fixed this run, punch-list #2)** — `handler.py` increments a
      per-user `leaderboard` on every correct count; a new **`!counttop`** command (alias `!ct`) shows
      the full standings and **`!count_info`** now carries a top-3 field. Rendering lives in
      `cogs/counting/leaderboard.py` over the pure `game_logic.top_counters`; previously the tally was
      dead state (incremented but never displayed).
- [x] **Rules affordance** — `!count_rules` (`counting_cog.py:566-595`).
- [x] **Info affordance** — `!count_info` shows current count, mode, turns, reset flag, range/step.
- [x] **Consistent copy/embeds** — clean embeds; transient `delete_after` admin replies keep channels
      tidy.

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — playing is just typing the next number; admin setup is one panel.
- [x] **Mode discovery for admins** — `start_match` lists valid modes on error.
- [ ] **Mode/leaderboard discovery for players** — a player can't easily see "what mode is this / how
      am I doing" without an admin or `count_info`; the leaderboard is hidden. → folded into #2.

### D. Edge cases & lifecycle — "works as intended"
- [x] **Concurrency** — per-channel `scope_locks` serialise validate+mutate; apply (Discord I/O) runs
      outside the lock (`counting_cog.py:715-730`).
- [x] **Persistence** — state is DB-persisted (`_save_guild`), so counting **survives restart**
      (better than ADR-002 in-memory games); save errors propagate to the managed-task layer (RC-15,
      `counting_cog.py:90-102`).
- [x] **Guild teardown** — `_drop_scope_locks_for_guild` hook releases locks on guild removal
      (`counting_cog.py:69-83`).
- [x] **Permissions hardened** — `is_staff_or_owner` gates on **real Discord tier**, not role names
      (BUG-0012 fix, `counting_cog.py:143-163`); regression-tested.
- [x] **Channel-create/delete failures** handled with explicit `Forbidden`/`Exception` branches
      (`counting_cog.py:288-310,399-421`).

### E. Money-safety integration — N/A (no economy surface; no wagering).

### F. Wiring & discoverability
- [⚠] **Registry entry_points are admin-only** — `entry_points: ["countingmenu"]`
      (`subsystem_registry.py`), which is `@staff_or_owner`. There is **no player-facing entry point**;
      a player discovers counting only by being in a counting channel. `count_info`/`count_rules` are
      public commands but aren't registered entry points. → punch-list #3.
- [x] **Help + Games hub** — registered `parent_hub: games`, `hub_group: activities`; Help hook returns
      the (admin) hub.
- [x] **Configurable** — turns, reset-on-wrong, skip-step are per-channel admin toggles.

### G. Tests & evidence (required for ✔)
- [x] **Loop/mode tests** — `tests/unit/cogs/test_counting_modes.py`,
      `test_counting_handler.py`, `test_counting_parsing.py`.
- [x] **Edge/permission tests** — `test_counting_permissions.py` (BUG-0012 guard),
      `test_counting_channel_select.py`.
- [x] **Leaderboard test** — `tests/unit/cogs/test_counting_leaderboard.py` (ranking math + the
      `!counttop`/`count_info` embeds), shipped with the #2 fix this run.
- [ ] **Live walkthrough recorded** — pending. → punch-list #4.
- [ ] **Owner ✔** — pending. → punch-list #5.

## Punch-list (clear these to certify)

1. **Decision: should counting reward XP/coins?** Today it rewards a visible leaderboard but no
   game_xp/coins. Either wire correct counts into `game_xp` (the activity-game pattern) **or** the
   owner waives it (counting is a collaborative streak, reward-free by design). Needs an owner call.
2. ✅ **DONE this run — leaderboard surfaced.** `!counttop` + a `count_info` top-3 field
   (`cogs/counting/leaderboard.py`, tested). The previously-dead tally is now player-visible.
3. **Player-facing discovery** — add a player entry point (e.g. surface `count_info`/`count_rules`/the
   new `counttop` as the unit's player entry) so counting isn't admin-only in the registry.
4. **Live walkthrough** — `/verify-bot` boot + a scripted play-through of a couple of modes (normal +
   one exotic, e.g. prime/random) showing validate/reset/turns, with screenshots, attached here.
5. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move," resolving #1.

## Evidence

- **Tests:** `tests/unit/cogs/test_counting_modes.py` · `test_counting_handler.py` ·
  `test_counting_parsing.py` · `test_counting_permissions.py` · `test_counting_channel_select.py` ·
  `test_counting_leaderboard.py` (new, #2 fix)
- **Walkthrough:** pending (punch-list #4)
- **Owner sign-off:** pending (punch-list #5)

## Verdict

Counting is **deep and well-engineered** — 11 modes, math-expression parsing, DB-persisted
restart-safe state, scope-locked concurrency, and a real security hardening (BUG-0012). The
**invisible-leaderboard** gap (#2) was **closed this run** — the standings are now player-visible via
`!counttop` + `count_info`. It is **not yet `✔ certified`**: what remains is **admin-only discovery**
(#3) and the **reward decision** (#1), then the walkthrough (#4) + owner sign-off (#5). The assess →
close loop the framework exists for is demonstrated here: assess surfaced the dead-state leaderboard,
the same PR shipped the fix.
