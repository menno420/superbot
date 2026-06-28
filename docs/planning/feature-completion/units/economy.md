# Economy — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `economy` · **Type:** server-fn · **Family:** economy
> **State:** ◐ assessed · **Assessed:** 2026-06-28 · **Certified:** —
> Source: `disbot/cogs/economy_cog.py` (commands + `!economymenu`/`/economy` + Help hook) ·
> `disbot/views/economy/` (`main_panel.py` `EconomyPanelView` · `work_panel.py` · `shop_panel.py`) ·
> `disbot/services/economy_service.py` (the single audited money seam) ·
> `disbot/services/economy_helpers.py` (jobs/shop/daily tables) ·
> `disbot/services/shop_purchase_workflow.py` · `disbot/utils/db/economy.py` ·
> `disbot/cogs/economy/schemas.py` (Phase-1 bindings) · `disbot/utils/settings_keys/economy.py`

> Assessed during the completion-first arc (Q-0209). Core economy (daily · work · shop · balance) is
> **money-safe and fully audited**: every coin mutation goes through `economy_service`
> (credit/debit/transfer/bet_and_settle/refund), pinned by the INV-F AST invariant, with atomic
> transfers and `economy_audit_log` rows + `EVT_BALANCE_CHANGED` on every change. It has a persistent
> panel with no dead-ends and Help integration. The honest gaps are **best-in-class breadth** — no
> public user-to-user `give`/`pay` command (the `transfer()` primitive exists but is unexposed), no
> leaderboard of its own (delegated to the Leaderboard unit), no bank/wallet split, **no admin
> balance panel** (set/add/reset), and a **hardcoded, non-configurable currency** — plus the daily/work/
> shop tables being static-in-code. Scope decisions, not defects.

## Rubric (server function)

### A. Functional completeness — "does its job, in every case"
- [x] **Core promise delivered** — `!daily` (6 streak-weighted rarity tiers), `!work`/`!joblist`
      (per-job pay + mastery bonus), `!shop`/buy (unique items via the purchase workflow), `!balance`
      (`bal`/`wallet`) — all on `EconomyPanelView` (`economy_cog.py`, `views/economy/`).
- [ ] **Every best-in-class sub-option exists** — ❌ **partial.** **Missing vs UnbelievaBoat/MEE6:**
      public user-to-user `give`/`pay` command (primitive exists, no command) · bank vs wallet split ·
      robbery/crime risk mechanic · income/multiplier roles · roles-for-currency shop · seasonal/event
      economy. → punch-list #2.
- [x] **Failure modes honest** — `InsufficientFundsError` raised (not swallowed); transfer rejects
      self-pay and ≤0 amounts; cooldowns enforced both command-side and view-side
      (`economy_service.py`).
- [x] **Idempotent / atomic** — daily uses a conditional `claim_daily_if_ready()` UPDATE (no
      double-claim race); transfers wrap two UPSERTs + the audit insert in one `conn.transaction()`;
      shop purchase is a workflow-owned transaction (Q-0071).

### B. Reachability & UI — "the most convenient way"
- [x] **A command panel exists** — `EconomyPanelView` (persistent, registered via `@register`): Daily ·
      Work · Shop · Balance · Inventory · Jobs · Treasury · Overview buttons across rows; restored on
      restart (`views/economy/main_panel.py`).
- [x] **Reachable every natural way** — `!economymenu` (persistent) + `/economy` (ephemeral) + the
      individual commands + Help hook; Inventory + Treasury are hub children (`subsystem_registry.py`).
- [ ] **Integrated into the Setup wizard** — ⚠️ **N/A by design (Phase 1).** Economy declares only
      bindings (the economy-log channel auto-provisions); no participation schema yet (deferred to
      Phase 2c, `cogs/economy/schemas.py`). Acceptable waiver — there is little an operator must
      configure at onboarding. → note, not a blocker.
- [x] **Return navigation** — the prior disabled-dropdown dead-end was fixed (`_WorkResultView` Back
      button); every ephemeral sub-view carries a `_back_target` chain back to Economy.
- [x] **In-place, not spammy** — the persistent panel edits in place; sub-views replace + Back
      re-renders.

### C. Convenience
- [ ] **Admin balance ops** — ❌ **missing.** No `!set`/`!add`/`!reset balance` operator commands and
      no admin economy panel; only `!setlogchannel` (administrator, audited binding). → punch-list #3.
- [x] **Sensible defaults** — daily 6 tiers (Common 500–999 … Mythic 5000); work base 50–1200 + 1%/
      completion mastery (cap 100%); 3 shop items; daily 24h / work 1h cooldowns
      (`economy_helpers.py`).
- [x] **Clear feedback** — daily shows tier + emoji + coins + new balance + streak + odds; work shows
      job + earned + XP + new balance + mastery; shop confirms item + price + new balance; insufficient
      funds shows the balance.

### D. Authority & safety
- [x] **Authority re-checked** — user surfaces are self-gating (your own wallet); cooldown re-checked
      **after** deferral (race-safe); shop affordability re-checked inside the purchase workflow;
      `!setlogchannel` is `administrator`-gated.
- [x] **All money mutations through the audited seam** — `economy_service` is the single writer;
      INV-F (`tests/unit/invariants/test_inv_f_economy_service.py`, AST) forbids direct
      `db.add_coins`/`db.set_coins` outside the service; every call writes `economy_audit_log` + emits
      `EVT_BALANCE_CHANGED`.
- [x] **Resource creation safe** — the economy-log channel auto-provisions on ready/join; the channel
      pointer is set via `BindingMutationPipeline` (audited).
- [x] **Reuses governance** — capabilities declared (`economy.currency.*`, `economy.shop.*`,
      `economy.settings.configure`); no second allowlist.

### E. Configuration
- [x] **Binding routes through the pipeline** — the log channel via `BindingMutationPipeline` (audited);
      no raw-key writes.
- [ ] **Tunable settings** — ⚠️ **none in Phase 1.** Currency name/emoji is **hardcoded** (`🪙`
      "coins", not guild-configurable); daily tiers, work pay, and shop prices are **static in code**
      (`economy_helpers.py`), not operator-tunable. → punch-list #4 (currency-name) / #2 (richer config).
- [x] **`settings_keys`** — no live KV scalars; the legacy `ECONOMY_LOG_CHANNEL` key is superseded by
      the binding lane.

### F. Wiring & discoverability
- [x] **Registry** — key `economy`, `category: economy`, `visibility_tier: user`,
      `entry_points: [economymenu, daily, work, balance]`, related `[inventory, mining]`,
      `ui_priority: 10`, 5 capabilities (`subsystem_registry.py`).
- [x] **Discoverable in Help** — `build_help_menu_view` hook + `/economy`.
- [x] **Homed in `ownership.md`** — `services/economy_service.py` owns every coin-balance mutation
      (INV-F).

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_economy_service.py` (credit/debit/transfer/bet_and_settle audit +
      emit; insufficient-funds; ≤0 rejection); `test_economy_db_txn.py` (conditional debit, upsert,
      audit insert, flow aggregations); view-lifecycle + work-result + treasury/inventory button tests.
- [x] **Authority/atomicity tests** — `test_economy_service_concurrent.py` (20 concurrent ops emit
      per-call, no silent collapse); transfer transaction isolation.
- [x] **Mutation-seam tests** — INV-F AST fence.
- [ ] **Live walkthrough recorded** — pending. → punch-list #5.
- [ ] **Owner ✔** — pending. → punch-list #6.

## Punch-list (clear these to certify)

1. **Public `give`/`pay` command** *(deepening, turn-key)* — expose the existing audited
   `economy_service.transfer()` as a user command (self-pay + amount validation already enforced at the
   seam). The lowest-effort, highest-value completeness gap.
2. **Best-in-class breadth (rubric A)** *(owner-paced, deepening)* — bank/wallet split · robbery/crime ·
   income/multiplier roles · roles-for-currency shop · richer operator-tunable daily/work/shop config ·
   seasonal events.
3. **Admin balance panel (rubric C)** *(deepening)* — `!set`/`!add`/`!reset balance` operator commands
   (or panel buttons), each through `economy_service` (audited) — today there is no operator money tool
   beyond the primitives.
4. **Configurable currency name/emoji** *(deepening)* — a guild-level currency-name override instead of
   the hardcoded `🪙`/"coins".
5. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + scripted click-through (panel →
   daily → work → shop buy → balance), with screenshots.
6. **Owner sign-off** — maintainer uses it and confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_economy_service.py` · `…/test_economy_service_concurrent.py` ·
  `tests/unit/db/test_economy_db_txn.py` · `tests/unit/invariants/test_inv_f_economy_service.py` ·
  `tests/unit/views/test_economy_*.py`
- **Walkthrough:** pending (punch-list #5)
- **Owner sign-off:** pending (punch-list #6)

## Verdict
Economy's **core loop is money-safe and fully audited** — one mutation seam (INV-F-pinned), atomic
transfers, audit + event on every change, a persistent dead-end-free panel, and strong concurrency
tests. It is **not yet `✔ certified`**: the headline gaps are a missing **public `give`/`pay`** (#1,
turn-key), **best-in-class breadth** (#2), an **admin balance panel** (#3), and **hardcoded currency** /
no operator-tunable config (#4) — plus the owner walkthrough/sign-off (#5/#6). No safety/audit/dead-end
issues found.
