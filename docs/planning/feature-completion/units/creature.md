# Creatures — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `creature` · **Type:** game · **Family:** activity
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> **Deepened:** 2026-06-29 — punch-list #1 (game panel), #2 (interactive dex browser), #3
> (`entry_points`), #5 (battle settle-once) **shipped** (PR #1546); #4 was a no-op (the accept
> path already responds before the slow resolve). Remaining to certify: #6 live walkthrough + #7
> owner sign-off (both `[owner]`).
> Source: `disbot/cogs/creature_cog.py` (catch/dex) · `disbot/cogs/creature_battle_cog.py` (PvP) ·
> `disbot/views/creature_battle/` (challenge · rematch · render) ·
> `disbot/services/creature_workflow.py` · `disbot/services/creature_battle_service.py` ·
> `disbot/utils/creatures/` (battle · catalog · encounters) · `disbot/utils/db/games/creatures.py` +
> `creature_battles.py`

> Assessed during the completion-first deepening run (Q-0209). Creatures is a catch-and-collect
> activity game with a **level-normalized 6v6 PvP** battle engine (anti-P2W: both teams flattened to
> level 50, type matchups decide). The combat domain is pure, deterministic, and well-tested; the
> catch/battle loops are money-free and atomic. The **headline completeness gap is real and a rubric-B
> miss**: Creatures is **hub-less v1** — there is **no interactive game panel** and **no interactive
> dex browser** (catch/dex are command + Help-embed only; the only views are the transient battle
> challenge/rematch). That, plus a registry `entry_points` discoverability gap and an optional
> settle-once on battle resolution, is the path to certification.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes/loop reachable** — catch (`!catch`, `creature_cog.py:51`), collection/dex (`!dex`/
      `!dextop`, `creature_cog.py:76`), level-normalized **PvP battle** (`!cbattle @user`,
      `creature_battle_cog.py:55`), battle records + ladder (`!cbrecord`/`!cbattletop`). Catch →
      collect → battle → resolve → rematch flows cleanly.
- [x] **Every standard action exists** — rarity-weighted encounter + level-scaled catch roll (capped
      95%, `utils/creatures/encounters.py:53`); 6v6 turn-based combat with a symmetric 6-element type
      chart (`utils/creatures/battle.py:73`); teams normalized to level 50 (`battle.py:211`, anti-P2W).
- [x] **Loop runs start→finish** — catch logs to collection + awards XP in one transaction
      (`creature_workflow.py:60`); battle resolves + records both fighters + awards winner XP in one
      transaction (`creature_battle_service.py:171`); result embed carries a 🔄 Rematch.
- [x] **No dead-end/placeholder controls** — the battle result view carries a rematch button; declined
      / timed-out challenges edit to a clear notice and stop. No "coming soon"/disabled-no-explanation.
- [x] **Rewards wired** — catch + battle-win XP both route through `game_xp_service.award()`
      (shared game-XP track `GAME_CREATURE`); no duplicated XP path.

### B. UI & buttons — "right buttons in the right places"
- [ ] **A game panel exists** — ❌ **NO (headline gap).** Creatures is **hub-less v1**: there is no
      interactive `HubView`/panel summarizing the game and offering its modes. It is surfaced only via
      the Help hook embed (`creature_cog.py:137`) + typed commands. The registry comment names "an
      actionable in-panel surface … a later slice" (`subsystem_registry.py:320`). → punch-list #1.
- [ ] **Every action has a control in the right place** — ❌ **partial.** The battle has buttons
      (Accept/Decline/Rematch); catch and dex have **no buttons** — `!catch` is one-shot, `!dex` is a
      static embed with no interactive browse/sort/filter. → punch-list #1/#2.
- [x] **Rules / how-to affordance** — the Help hook embed documents catch flavor, collection, the
      level-normalized PvP mechanic, and all six commands (`creature_cog.py:146`).
- [x] **Return navigation everywhere** — ✅ **no trapped views** in the battle path: challenge/rematch
      are transient `BaseView` game-state views (correctly no `SUBSYSTEM`); every terminal (decline,
      timeout, resolved) stops the view or hands to the rematch loop. *(The catch/dex commands post
      plain embeds — no view to trap; the gap there is the missing panel, #1, not a trapped view.)*
- [x] **Terminal state correct** — challenge buttons disable + message edits on accept/decline/timeout;
      `_resolved` guard stops a stale timeout from clobbering a resolved battle
      (`challenge.py:116`, mirrors the BUG-0013 class).
- [x] **Consistent copy/embeds** — house-style; the battle render marks 💀 fainted + winner + records
      (`render.py:63`); no debug/placeholder strings.

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — catch is one command; the battle result's 🔄 Rematch re-issues a fresh
      challenge (clicker becomes challenger) **without retyping** `!cbattle @x` (`rematch.py:28`).
- [x] **Replay/rematch without retyping** — ✅ rematch button on the result embed, tappable by either
      fighter (custom `interaction_check`, `rematch.py:44`).
- [x] **Sensible defaults** — catch uses the player's current level automatically; PvP auto-builds
      teams from the collection at the normalized level (no move-picking/loadout step).
- [ ] **Reachable the natural way** — ⚠️ **partial.** Commands ✅, Help hook ✅, Games hub child ✅ —
      but with **no panel** the "Games hub → Creatures → click to play" path dead-stops at an embed,
      and the three battle commands are missing from registry `entry_points` (#3). → folded into #1/#3.

### D. Edge cases & lifecycle — "works as intended"
- [x] **Timeout** — challenge 60 s; `on_timeout` fires only if unanswered (accept/decline call
      `self.stop()`); edits to an expiry notice (`challenge.py:105`).
- [ ] **Expired/stale interaction** — accept/decline use direct `interaction.response.edit_message`
      **without `safe_defer`**, then call the battle service *after* the response; on a slow resolve
      the follow-up could miss the 3 s window. Low risk (mirrors deathmatch/rps), but not hardened. →
      punch-list #4 (minor).
- [x] **Authority re-checked** — challenge is author-locked to the opponent (`BaseView`); rematch
      allows only the two fighters (`rematch.py:44`); third parties get an ephemeral rejection.
- [ ] **Concurrency / settle-once** — battle resolution is one atomic transaction, but there is **no
      settle-once / battle-id guard**: two simultaneously-accepted challenges between the same pair
      would each resolve + record. Idempotent-ish (record writes are increments), but a player could
      see two result embeds. → punch-list #5 (low-risk).
- [x] **Restart per ADR-002** — collection + battle records persist in DB rows; in-flight challenge
      messages orphan harmlessly on restart; no state corruption; **no money at stake**.

### E. Money-safety integration
- [x] **No wagering** — Creatures is **free by design**: catch and battle award **game XP only**, no
      coins, no escrow (`creature_workflow.py:84`, `creature_battle_service.py:173`). `economy` is a
      *soft* relation only (the game works when economy is disabled). No mint window.

### F. Wiring & discoverability
- [ ] **Registry `entry_points` complete** — ⚠️ key `creature`, but `entry_points: [catch, dex]`
      **omits** `cbattle` / `cbrecord` / `cbattletop` (defined in the sibling `creature_battle_cog.py`,
      same subsystem per its docstring). The Help hook manually lists all six so user-facing Help is
      intact, but the registry entry under-declares the unit's surface. → punch-list #3 (minor).
- [x] **Discoverable in Help** — Help hook returns the overview embed; Games-hub child
      (`parent_hub: games`, `hub_group: activities`).
- [x] **Settings** — none needed for v1 (free progression game).

### G. Tests & evidence (required for ✔)
- [x] **Loop tests** — catch atomicity/flee/level-up (`test_creature_workflow.py`); PvP team-build +
      resolve + record (`test_creature_battle_service.py`); encounter/catch-chance math
      (`test_creature_encounters.py`); catalog load (`test_creature_catalog.py`).
- [x] **Battle-engine tests** — damage, type effectiveness, 6v6 resolution, turn log
      (`test_creature_battle.py`); + Monte-Carlo balance sim + runtime↔sim parity
      (`test_creature_battle_sim.py`, `test_creature_sim_engine_parity.py`).
- [x] **Edge tests** — challenge timeout race (`test_creature_challenge_timeout.py`), rematch
      interaction gating (`test_creature_rematch.py`), result render (`test_creature_battle_render.py`),
      DB CRUD + leaderboards (`test_creature_db.py`, `test_creature_battles_db.py`).
- [x] **Money tests** — n/a (free game).
- [ ] **Live walkthrough recorded** — pending. → punch-list #6.
- [ ] **Owner ✔** — pending. → punch-list #7.

## Punch-list (clear these to certify)

1. ✅ **Build the game panel (headline).** **Shipped (PR #1546).** `views/creature/menu.py` —
   `CreatureMenuView` (`HubView`, `SUBSYSTEM = "creature"`): 🐾 Catch (in place) · 📖 Dex (browser) ·
   ⚔️ Challenge (UserSelect → the existing challenge flow) · 🏆 Ladder · 📖 How to play · auto
   📚 Help / ↩ Games nav. Reached via `!creatures` / `!creaturemenu` and the live Help hook (both
   the catch cog and the PvP cog return it). The Games-hub → Creatures path now lands on a playable
   surface.
2. ✅ **Interactive dex browser.** **Shipped (PR #1546).** `CreatureDexView` — an element-filter
   `Select` over the collection + ◀ Back to the menu + standard nav.
3. ✅ **Registry `entry_points` gap.** **Shipped (PR #1546).** The `creature` entry now declares
   `creatures` / `catch` / `dex` / `cbattle` / `cbrecord` / `cbattletop`.
4. ~~**Defer on the battle-resolve path.**~~ **No-op** — the accept callback already calls
   `interaction.response.edit_message` (the response) *before* `resolve_and_record_pvp`, so the slow
   resolve runs after the interaction is acknowledged; the follow-up uses the 15-min `followup` window.
5. ✅ **Battle settle-once guard.** **Shipped (PR #1546).** `CreatureBattleChallengeView` now mixes in
   `SettleOnceMixin` and claims the transition at the top of accept/decline, so a double-click can't
   resolve + record the battle twice. *(Cross-view simultaneous-challenge dedup — a per-pair active
   registry — remains a possible deepening, but is lower-risk than the double-click it now guards.)*
6. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (catch →
   dex → challenge → accept → battle → rematch; check the ladder), with screenshots.
7. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move."

## Evidence
- **Tests:** `tests/unit/services/test_creature_workflow.py` · `…/test_creature_battle_service.py` ·
  `tests/unit/utils/test_creature_{battle,catalog,encounters}.py` ·
  `tests/unit/views/test_creature_{challenge_timeout,battle_render,rematch}.py` ·
  `tests/unit/db/test_creature_db.py` · `…/test_creature_battles_db.py` ·
  `tests/unit/tools/test_creature_{sim_engine_parity,battle_sim}.py`
- **Walkthrough:** pending (punch-list #6)
- **Owner sign-off:** pending (punch-list #7)

## Verdict
Creatures has a **strong, well-tested engine** — a pure deterministic level-normalized 6v6 battle
(anti-P2W), atomic money-free catch/battle loops, a trap-free battle path with a rematch affordance,
and parity-checked balance sims. It is **further from `✔ certified` than Mining**, on a genuine
**rubric-B completeness gap**: it is hub-less v1 with **no interactive game panel** (#1) and **no
interactive dex browser** (#2), so the Games-hub path stops at a static embed. With those built (plus
the minor `entry_points`/defer/settle-once items #3–#5) and the owner walkthrough/sign-off (#6/#7),
it becomes a `✔` candidate. No money/restart issues; no trapped views in the battle path.
