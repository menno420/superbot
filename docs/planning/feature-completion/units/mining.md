# Mining — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `mining` · **Type:** game · **Family:** activity
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/mining_cog.py` · `disbot/views/mining/*.py` (13 panels) ·
> `disbot/services/mining_workflow.py` (the sole write seam, RS02/Q-0071) ·
> `disbot/utils/mining/*.py` (17 domain modules) · `disbot/utils/db/games/mining_*.py`

> Assessed during the completion-first deepening run (Q-0209). Mining is by far the **largest** S1
> game — a grid-navigation core loop plus 12 supporting systems (harvest · craft · market · gear/
> loadouts · descent · workshop/repair · vault · skills · forge · home · titles). It is structurally
> complete, money-safe (every coin move is one audited transaction), and has the **deepest test
> coverage of any game** (41 test files incl. a write-boundary ratchet). The punch-list is short:
> one minor convenience affordance (a dedicated how-to button) plus the standard
> walkthrough/sign-off — this is a strong **✔-ready candidate** pending the owner walkthrough.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes/loop reachable** — an **activity** game (no PvP/tournament by concept). 13 reachable
      actions: ⛏️ Mine grid (`grid_mine_view.py:84`), 🌲 Harvest (`mining_cog.py:117`), 🗺️ Explore
      (world hub forward, `main_panel.py:225`), 🛠️ Craft (`recipe_browser.py`), 💰 Market sell/buy
      (`market_panel.py`), 🧰 Gear/Loadouts (`gear_panel.py`), ⬇️ Descend (`mining_cog.py:439`),
      🔧 Workshop repair/quick-craft (`workshop_panel.py`), 🏦 Vault (`vault_panel.py`), 🌳 Skills
      (`skills_panel.py`), 🔥 Forge (`forge_panel.py`), 🏠 Home (`home_panel.py`), 🏆 Titles
      (`titles_panel.py`).
- [x] **Every standard action exists** — dig is locomotion (N/S/E/W/Deeper/Up move-and-mine,
      `grid_mine_view.py:147`); energy frequency-brake instead of cooldown (`utils/mining/energy.py`);
      loot tables shift with depth (`utils/mining/rewards.py:90`); wear/repair, deeper ladders, set
      bonuses, skills. No standard activity-game action is silently absent.
- [x] **Loop runs start→finish** — `!mine` → grid navigator → dig (re-renders in place) → loot/XP →
      ↩ Mining Menu. Every workflow op is one `db.transaction()` (`mining_workflow.py`, Q-0071).
- [x] **No dead-end/placeholder controls** — verified: no "coming soon"/disabled-no-explanation
      buttons; the `no_dead_end` arch guard (#1529) is clean on the mining views.
- [x] **Rewards wired** — game XP via `game_xp_service` inside the op's transaction
      (`mining_workflow.py`); coins via `economy_service.{credit,debit}_in_txn` — never ad-hoc
      `db.update_coins`.

### B. UI & buttons — "right buttons in the right places"
- [x] **Game panel exists** — `MiningHubView(PersistentView, SUBSYSTEM="mining")` (`main_panel.py:146`):
      Mine · Harvest · Explore · Character · Gear · Workshop, over a net-worth + action-guide embed
      (`_ACTIONS_GUIDE`, `main_panel.py:47`). Persistent (auto-restored on boot).
- [x] **Every action has a control** — primary actions on the hub; sub-actions on the Character-hub,
      Workshop-hub, Gear, Market, Vault, Skills, Forge, Home, Titles sub-panels; modals
      (vault move / save-loadout / build) submit → refresh parent in place.
- [ ] **Rules / how-to affordance** — **partial:** the hub embed carries an inline `_ACTIONS_GUIDE`
      routing guide and per-panel "how to use" blurbs, and the Recipe browser is `📖 Recipes`, but
      there is no single dedicated 📖 How-to button at the hub (the bar Fishing/Blackjack meet). →
      punch-list #1 (minor).
- [x] **Return navigation everywhere** — ✅ **no trapped views.** Every panel is a `HubView` with
      `SUBSYSTEM = "mining"` so `attach_standard_nav` adds 📚 Help + ↩ Games (12 views verified); the
      action-loop `MineGridView` is a `BaseView` (120 s, intentional) but carries explicit
      **↩ Mining Menu** + 📚 Help buttons (`grid_mine_view.py:202,226`). `test_mining_back_to_games.py`
      / `test_mining_back_to_help.py` pin the nav.
- [x] **Terminal state correct** — action loop re-renders in place; `BaseView`/`HubView` disable
      controls + edit on timeout. No money/round terminal to settle (activity game).
- [x] **Consistent copy/embeds** — house-style emojis/titles; no debug/placeholder strings found.

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — dig re-renders the grid in place (no re-issue); Equip-Best fills every
      slot in one click; stash-all-ore is one button (`vault_panel.py`).
- [x] **Replay/repeat without retyping** — the grid navigator stays live across digs; quick-craft
      re-crafts + auto-equips the last-broken item (`mining_workflow.quick_craft`); `!fastmine`.
- [x] **Sensible defaults + presets** — named gear **loadout presets** (save/apply/delete, cap 10,
      `mining_cog.py:359`); apply equips every still-owned item + reports the rest.
- [x] **Reachable the natural way** — `!minemenu`/`!mine` (+ ~15 commands) **and** the Games hub
      (`parent_hub: games`) **and** the Help hook (`build_help_menu_view`, `mining_cog.py:66`).

### D. Edge cases & lifecycle — "works as intended"
- [x] **Timeout** — `MineGridView` 120 s, panels 180 s; disable + edit on timeout (`views/base.py`).
- [x] **Expired/stale interaction** — every DB-bearing callback opens with `safe_defer` then
      `safe_edit` (all 13 view files use `safe_defer`; e.g. `grid_mine_view.py:124`).
- [x] **Authority re-checked** — `BaseView.interaction_check` pins the invoker per callback; admin
      commands gate on `guild_permissions.administrator` (`mining_cog.py:756`).
- [x] **Concurrency** — one `db.transaction()` per op; energy is timestamp-settled on read (no ticker,
      ADR-001/002); wear writes commit inside the caller-owned transaction
      (`mining_workflow.py:173`). No coin/round race (no two-party settle).
- [x] **Restart per ADR-002** — all state in DB rows (position/depth/energy/equipment/inventory/vault/
      skills/structures); no in-memory game state to lose.

### E. Money-safety integration
- [x] **Audited seam** — sell/buy/repair/vault-upgrade/forge-build/home-build all move coins through
      `economy_service.{credit,debit}_in_txn` inside `db.transaction()` with traceable reason tags
      (`"mining:sell_ore"`, `"mining:buy_gear"`, …); `InsufficientFundsError` rolls the whole op back.
- [x] **No mint window** — every coin source is consumptive (sell mined ore) or an external earn; no
      free-coin path. Inventory debit + coin credit are atomic.
- [x] **Recovery paths** — all-or-nothing transactions; no escrow to strand (single-player game).

### F. Wiring & discoverability
- [x] **Registry** — key `mining`, `entry_points: [minemenu, mine]`, `parent_hub: games`,
      `hub_group: activities`, caps `mining.resource.mine` / `.view`, `dependencies: [economy]`
      (`subsystem_registry.py:259`).
- [x] **Help + Games hub** — `build_help_menu_view` returns the live overview + hub; Games child.
- [x] **Settings** — no per-guild settings by design (a personal progression game); economy
      dependency supplies the coin rails.

### G. Tests & evidence (required for ✔)
- [x] **Loop tests** — mine/explore/harvest/market/craft/world covered across `tests/unit/cogs/`,
      `tests/unit/services/` (grid_workflow, forge, cook, loadout), and the economy sim
      (`test_mining_economy_sim.py`).
- [x] **Edge tests** — energy settle, capacity cap, gear wear, descent gating, guild scope, loadout
      reversibility, in-place card re-render (`test_mining_energy.py`, `…_capacity.py`,
      `…_gear_wear_db.py`, `…_guild_scope.py`, `…_inplace_cards.py`).
- [x] **Money tests** — `test_mining_workflow_characterization.py` pins the audited reason tags +
      user-visible economy messages; `test_mining_market.py` covers sell/buy.
- [x] **Invariant** — `test_mining_write_boundary.py` AST-ratchets that no cog/view writes the DB
      directly (every mutation goes through `services.mining_workflow`).
- [ ] **Live walkthrough recorded** — pending. → punch-list #2.
- [ ] **Owner ✔** — pending. → punch-list #3.

## Punch-list (clear these to certify)

1. **How-to affordance** *(offline, minor)* — add a dedicated 📖 How-to button at the Mining hub (or
   a one-screen "how mining works" panel), mirroring Fishing/Blackjack. The inline `_ACTIONS_GUIDE`
   covers routing but a first-time player has no single rules surface.
2. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (mine the
   grid → descend → harvest → craft → market sell/buy → gear/loadout → workshop repair → vault
   deposit → skills → forge → titles → back to hub), with screenshots.
3. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move."

## Evidence
- **Tests:** 41 files under `tests/unit/{cogs,services,db,utils,views,invariants,tools}/test_mining_*.py`
  — incl. `test_mining_write_boundary.py` (invariant), `test_mining_economy_sim.py`,
  `test_mining_workflow_characterization.py`, `test_mining_back_to_{games,help}.py`.
- **Walkthrough:** pending (punch-list #2)
- **Owner sign-off:** pending (punch-list #3)

## Verdict
Mining is the **most feature-complete game in the bot** — 13 wired action systems, no trapped views,
fully audited transactional economy with traceable reason tags, and the deepest test coverage of any
unit (41 files + a write-boundary ratchet). It is **not yet `✔ certified`**: what remains is a minor
how-to affordance (#1) and the owner-paced live walkthrough + sign-off (#2/#3). No money/restart/
dead-end issues found. The code-side completion bar is essentially met — a strong **✔-ready
candidate** pending the owner walkthrough.
