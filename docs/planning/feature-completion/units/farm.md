# Chicken farm — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `farm` · **Type:** game · **Family:** activity
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/farm_cog.py` · `disbot/views/farm/menu.py` · `disbot/services/farm_workflow.py` ·
> `disbot/utils/farm/farm.py` (domain) · `disbot/utils/db/games/` (chicken_farm row)

> Assessed during the completion-first deepening run (Q-0209). The farm is a small, clean **idle**
> game — passive egg accrual (no ticker, ADR-001/002-safe), collect → coins+XP, shop (buy hen / upgrade
> coop). It is structurally complete and money-safe with strong domain tests; the punch-list is a short
> hardening list (interaction-deferral, double-settle window, view/integration tests) plus the standard
> walkthrough/sign-off.

## Rubric (game)

### A. Game-loop completeness — "all the functions"
- [x] **Modes/loop reachable** — single-concept idle loop (lay → collect → spend); two spend options
      (buy hen ↑ lay-rate, upgrade coop ↑ cap). No PvP/tournament by concept (correctly absent).
- [x] **Every standard action exists** — Collect, Shop (Buy hen / Upgrade coop), Refresh; "while you
      were away" idle summary (`farm_workflow.py:82`).
- [x] **Loop runs start→finish** — accrual computed from `(eggs, updated_at)` + elapsed, capped at coop
      capacity, sub-interval remainder preserved (idempotent settle; `farm.py:68`).
- [x] **No dead-end/placeholder controls** — both panels carry explicit nav (see B); no "coming soon".
- [x] **Rewards wired** — collect credits coins via `economy_service.credit_in_txn` + game XP, all
      inside one `db.transaction()` (`farm_workflow.py:114`).

### B. UI & buttons — "right buttons in the right places"
- [x] **Game panel exists** — `FarmMenuView` (🥚 Collect · 🛒 Shop · 🔄 Refresh), coop-fill gauge +
      countdown, balance, idle blurb (`menu.py:48`).
- [x] **Every action has a control** — collect/refresh on the menu; buy/upgrade on the Shop sub-panel.
- [ ] **Rules / how-to affordance** — partial: the menu embed *describes* the loop inline ("hens lay
      eggs… press Collect… visit the Shop"), but there's no dedicated 📖 how-to button (the bar Fishing
      now meets). → punch-list #4 (minor).
- [x] **Return navigation everywhere** — ✅ **no trapped views.** Both `FarmMenuView` and `FarmShopView`
      declare `SUBSYSTEM = "farm"` so `attach_standard_nav` adds 📚 Help + ↩ Games; the Shop also has an
      explicit ◀ Back that rebuilds the menu in place and `carry_back`s the target (`menu.py:233,275`).
- [x] **Terminal state correct** — idle game; buttons disable on view timeout; no stale clickable state.
- [x] **Consistent copy/embeds** — house-style; no debug/placeholder strings.

### C. Convenience — "the most convenient way"
- [x] **No needless clicks** — Collect / Buy / Upgrade are one click each; Shop opens instantly (no DB
      read on open).
- [x] **Replay/repeat without retyping** — Shop re-stickies with updated prices after each purchase; the
      menu stays live for repeated collects.
- [x] **Sensible defaults** — idle game needs no presets; prices scale automatically.
- [x] **Reachable the natural way** — `!farm`/`!chickenfarm`/`!coop` + the Games hub + Help hook + the
      Explore-world hub (`farm_cog.py:43,51,90`).

### D. Edge cases & lifecycle — "works as intended"
- [x] **Fresh-start safety** — epoch-0 timestamp normalized to *now* so a new farm doesn't retro-accrue
      a full coop (`farm_workflow.py:39`; `test_farm_workflow.py:24`).
- [x] **Timeout** — `HubView` 180 s; buttons disable + edit on timeout.
- [x] **Authority re-checked** — `BaseView.interaction_check` pins the author per callback.
- [ ] **Concurrency** — a rapid double-collect could in principle settle the same accrual twice (settle
      happens *before* the txn; no row lock). Low risk in practice (Discord serializes a user's button
      interactions), but not hardened. → punch-list #2.
- [x] **Restart per ADR-002** — all state in the `chicken_farm` row; settling is deterministic; no
      out-of-band tracker.

### E. Money-safety integration
- [x] **Audited seam** — collect credits + buy/upgrade debits all go through `economy_service`
      `*_in_txn` inside `db.transaction()`; `InsufficientFundsError` rolls back with a friendly message
      (`farm_workflow.py:132,210,270`); events emit post-commit.
- [ ] **No mint window** — within a transaction, yes; the *settle-before-txn* ordering leaves a narrow
      theoretical double-settle window under true concurrency (see D / punch-list #2). Not a live bug.
- [x] **Recovery paths** — no escrow to strand; coin moves are single audited writes.

### F. Wiring & discoverability
- [x] **Registry** — key `farm`, `entry_points: [farm]`, `parent_hub: games`, `hub_group: activities`,
      caps `egg.collect` / `coop.manage`, `soft_dependencies: [economy]` (`subsystem_registry.py:355`).
- [x] **Help + Games hub + Explore** — `build_help_menu_view` present; WorldEntry registered.
- [x] **Settings** — idle v1 has no per-guild settings by design.

### G. Tests & evidence (required for ✔)
- [x] **Domain tests** — 27 across `test_farm.py` + `test_farm_workflow.py`: fresh-start guard, accrual
      idempotence, capacity cap, remainder preservation, pricing monotonicity, can/can't-buy ceilings.
- [ ] **Workflow/view tests** — no integration tests for `collect`/`buy`/`upgrade` (txn + rollback)
      and no view-callback tests. → punch-list #3.
- [ ] **Live walkthrough recorded** — pending. → punch-list #5.
- [ ] **Owner ✔** — pending. → punch-list #6.

## Punch-list (clear these to certify)

1. **Interaction deferral on DB-bearing buttons** *(offline)* — `collect_btn`/`buy_btn`/`upgrade_btn`
   run a workflow op then `interaction.response.edit_message` with no `safe_defer` (`menu.py:198,254,267`);
   the mining panel defers before its DB op. On a slow DB this risks the 3 s response window. Defer
   first, then edit the original response. *(Contained, but changes the response pattern across the
   view — do it as its own focused slice with a view test, not bundled blind.)*
2. **Double-settle window** *(offline, low-risk)* — settle the accrual *inside* the transaction after a
   `FOR UPDATE` lock on the `chicken_farm` row (or re-settle post-lock), closing the rapid-double-click
   TOCTOU. Low priority (Discord queues per-user), architecturally cleaner.
3. **Workflow + view tests** — `collect` txn completes / `buy` insufficient-funds rolls back / `upgrade`
   price scales; plus a view-callback smoke test (mocked interaction).
4. **How-to affordance** *(minor)* — a dedicated 📖 button (mirrors Fishing/Blackjack), or expand the
   embed to explain the coop cap (accrual stops when full).
5. **Live walkthrough** — `/verify-bot` boot + scripted click-through (collect → shop → buy hen →
   upgrade coop → back → idle-accrual), with screenshots.
6. **Owner sign-off** — maintainer plays it and confirms "nothing left to add or move."

## Evidence
- **Tests:** `tests/unit/utils/test_farm.py` · `tests/unit/services/test_farm_workflow.py`
- **Walkthrough:** pending (punch-list #5)
- **Owner sign-off:** pending (punch-list #6)

## Verdict
The chicken farm is **structurally complete and money-safe** — a clean idle loop with audited
transactional economy, no trapped views, and strong domain tests. It is **not yet `✔ certified`**: the
punch-list is hardening (defer-on-DB #1, double-settle window #2, workflow/view tests #3) plus a minor
how-to affordance (#4) and the owner walkthrough/sign-off (#5/#6). No money/restart/dead-end issues.
