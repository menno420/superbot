# Fishing — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `fishing` · **Type:** game · **Family:** activity
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/fishing_cog.py` · `disbot/views/fishing/` (`cast_view.py` ·
> `menu.py` · `rod_shop.py` · `bait_shop.py`) · `disbot/services/fishing_workflow.py` ·
> `disbot/utils/fishing/` (domain) · `disbot/utils/db/games/fishing.py` · data:
> `disbot/data/fishing/fish.json`

> Assessed during the post-#1513 completion-first deepening run. Fishing is one of the bot's most
> feature-complete activity games — a real skill-moment cast loop, weather/venue depth, four craft
> paths, leaderboards, and a dex. The assessment surfaces a small, concrete punch-list whose headline
> is a **trapped-view navigation gap** in the two shop panels.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes reachable** — fishing is single-mode by concept (cast & catch), with **two venues**
      (Shore / Deepwater, `!sail`) that act as difficulty/content tiers (`fishing_cog.py:106`,
      `cast_view.py:99-104`). No PvP/tournament concept for a catch game (correctly absent).
- [x] **Every standard action exists** — cast → wait → bite → reel, plus a trophy **reel-fight**
      (`cast_view.py:230-374`), fakeouts, premature-reel grace, escape/snap. Benchmarked against
      best-in-class fishing minigames: nothing standard is missing.
- [x] **Loop runs start→finish** — `prepare_cast` → bite task → reel → `commit_catch`, resolving to a
      caught/got-away terminal in every branch (`cast_view.py:376-490`).
- [x] **No dead-end controls** — both terminal paths (landed **and** got-away) hand off to
      `_FishingDoneView` with **🎣 Cast again** + standard nav (`cast_view.py:532-569`), per the
      2026-06-23 owner directive.
- [x] **Rewards wired** — progression via `game_xp` (`GAME_FISHING`), collection log + trophy records;
      v1 deliberately has **no coins** (deferred owner question Q-0175) — that is a recorded design
      choice, not a gap.

### B. UI & buttons — "right buttons in the right places"
- [x] **Game panel exists** — `FishingMenuView` (🎣 Cast · ⛵ Set sail/Dock · 🎒 Rod · 🪱 Bait · 📖
      Fishdex), reached from `!fishing` and the Help hook (`menu.py:180-268`).
- [x] **Every action has a control in the right place** — cast/sail/rod/bait/dex on the menu;
      reel on the cast view.
- [~] **Rules affordance** — the menu embed *describes* the loop inline (`menu.py:56-65`); there is no
      dedicated "📖 Rules / how to play" button as the blackjack panel has. → punch-list #2 (minor).
- [ ] **Return navigation everywhere** — the **cast** flow has full nav (Cast again + Help + Games via
      `_FishingDoneView`). But the **Rod shop** and **Bait shop** are `BaseView` panels with **no back
      button** (`rod_shop.py:88`, `bait_shop.py:209`), and `FishingMenuView` **`self.stop()`s** when it
      opens them (`menu.py:236,253`) — so a player who opens Rod/Bait is **trapped** with no way back
      to the menu, Games hub, or Help. → **punch-list #1 (headline gap).**
- [x] **Terminal state correct** — disable-on-terminal + handoff to the Done view; the cast button
      label/style track the phase (`cast_view.py:445-447,182-192`).
- [x] **Consistent copy/embeds** — house-style embeds, shared colours (`GAME_COLOR`/`SUCCESS`/`ERROR`).

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — one **Reel** button drives the whole loop; the menu is one hop from cast.
- [x] **Replay without retyping** — **Cast again** on the Done view; **Set sail** keeps the menu so you
      can re-cast immediately (`menu.py:205-220`).
- [x] **Sensible defaults + presets** — energy gauge, daily shared forecast, equipped rod/bait folded
      into the cast automatically.
- [x] **Reachable the natural way** — `!fish`/`!fishing` + the Games hub (registry `parent_hub: games`)
      + the Help hook.

### D. Edge cases & lifecycle — "works as intended"
- [x] **Timeout** — `_VIEW_TIMEOUT = 45s` safety net; background tasks normally resolve first
      (`cast_view.py:509-520`).
- [x] **Expired / stale interaction** — `safe_defer`/`safe_edit` guard every callback; a dead token
      tears down silently (`cast_view.py:329-330,365-366,492-496`).
- [x] **Authority re-checked** — `interaction_check` pins the caster (`cast_view.py:500-507`); the menu
      is author-restricted via `HubView`.
- [x] **Concurrency** — `active_casts` set blocks a second simultaneous cast; each window carries a
      `_round_id` staleness token so a stale background task exits instead of false-failing
      (`cast_view.py:56-59,306-308`).
- [x] **Restart per ADR-002** — cast state is in-memory and not restart-safe (accepted); **no money
      is at stake** (v1 has no coins), and the collection log / XP are committed atomically on land.

### E. Money-safety integration
- [x] **Audited seam** — all writes go through `fishing_workflow` (`begin_cast`/`commit_catch`/
      `buy_rod`/`craft_*`); rod purchases spend coins through the audited workflow.
- [x] **No mint window** — the catch is rolled but **not written** until fully reeled
      (`cast_view.py:376-386`); a got-away path writes nothing.
- [x] **Recovery paths** — no escrow to strand (no wagering); coin spends are single audited writes.

### F. Wiring & discoverability
- [x] **Registry** — key `fishing`, `entry_points: [fish, fishlog]`, `parent_hub: games`,
      `hub_group: activities`, caps `fishing.catch.fish` / `fishing.collection.view`
      (`subsystem_registry.py:290`).
- [x] **Help + Games hub** — Help hook returns the live menu; listed under the Games hub.
- [x] **Settings** — fishing v1 has no per-guild settings by design (no coins/limits to configure yet).

### G. Tests & evidence (required for ✔)
- [x] **Loop tests** — `tests/unit/views/test_fishing_cast_view.py`,
      `tests/unit/utils/test_fishing_minigame.py`, `tests/unit/services/test_fishing_workflow.py`.
- [x] **Edge tests** — cast-view staleness/terminal + menu handoff
      (`test_fishing_cast_view.py`, `test_fishing_menu.py`); craft/bait/rod paths
      (`test_fishing_workflow_{bait,charm,rod}.py`).
- [x] **"Money" tests** — rod-spend + craft paths covered (`test_fishing_workflow_rod.py`,
      `test_fishing_rod_db.py`); no wagering to escrow-test.
- [ ] **Live walkthrough recorded** — pending. → punch-list #4.
- [ ] **Owner ✔** — pending. → punch-list #5.

## Punch-list (clear these to certify)

1. **Trapped shop views (headline).** Give `RodShopView` and `BaitShopView` return navigation — a
   "↩ Fishing menu" button (or convert them to `HubView` with `SUBSYSTEM = "fishing"` so
   `attach_standard_nav` adds 📚 Help + ↩ Games, the pattern `_FishingDoneView` already uses). Today
   opening Rod/Bait from the menu strands the player (the menu `self.stop()`s and the shops have no way
   back). Offline/contained; mind the menu↔shop import cycle (lazy-import or the HubView route).
2. **Rules affordance + minor UX** — a dedicated "📖 How to fish" button on the menu (the loop is only
   described in the embed body today); optionally a quick-rebet equivalent.
3. *(none — test coverage is strong; A/D/E/G loop+edge+money items are all green.)*
4. **Live walkthrough** — `/verify-bot` boot + scripted click-through (cast → trophy fight → got-away →
   menu → rod → bait → dex → sail), with screenshots, attached here.
5. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move," and resolves
   the deferred **fish-value/coins** question (Q-0175) — its answer may add an economy surface.

## Evidence

- **Tests:** `tests/unit/views/test_fishing_{cast_view,menu,rod_shop,bait_shop}.py` ·
  `tests/unit/utils/test_fishing_minigame.py` · `tests/unit/services/test_fishing_workflow*.py` ·
  `tests/unit/db/test_fishing_*_db.py`
- **Walkthrough:** pending (punch-list #4)
- **Owner sign-off:** pending (punch-list #5)

## Verdict

Fishing is **substantially complete and feature-rich** — a genuine skill-moment cast loop with trophy
fights, two venues, daily weather, four craft paths, leaderboards, and a dex, all on an audited write
seam with strong tests. It is **not yet `✔ certified`**: the one real UX-completeness gap is the
**trapped Rod/Bait shop views** (#1) — fix that and the menu is a fully-navigable place. Add a Rules
button (#2), record the walkthrough (#4), and get the owner's coins/sign-off call (#5). #1 and #2 are
a focused offline session; #4/#5 are owner-paced.
