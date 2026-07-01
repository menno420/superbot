# Treasury — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate; updated as the unit is assessed /
> certified. Source + merged PRs win. System: [`../README.md`](../README.md).

> **Unit:** `treasury` · **Type:** server-fn · **Family:** economy
> **State:** ◐ assessed · **Assessed:** 2026-06-29 · **Certified:** —
> Source: `disbot/cogs/treasury_cog.py` (`!treasury` group: contribute/grant + Help hook) ·
> `disbot/views/treasury/menu.py` (panel + Contribute modal) · `disbot/services/treasury_service.py`
> (contribute/disburse workflows) · `disbot/utils/db/treasury.py` (pool primitives) ·
> `disbot/views/economy/main_panel.py` (Economy-hub button) · folio economy

> Assessed during the completion-first arc (Q-0209). Treasury is the **server-owned collective coin
> pool** — the seam between the per-user economy and governance. Members contribute their own coins
> (a sink); managers (`manage_guild`) disburse from the pool to members. Both operations run **both
> legs on one connection inside a transaction** (Q-0071 contract) so a stale-balance race is impossible
> and coins are never minted (an underfunded pool/user writes nothing). The per-user coin legs audit via
> `economy_service` (`economy_audit_log` + `EVT_BALANCE_CHANGED`, with the manager recorded as actor on
> disburse). No server-level configuration by design (a collective resource, not a tunable). Gaps are
> cosmetic: no cog-level / modal-parse tests, and a soft-dependency note to document.

## Rubric (server function)

### A. Functional completeness
- [x] **Core promise delivered** — contribute (member → pool) + disburse (manager → member), end-to-end,
      transactional (`treasury_service.py`); structured `TreasuryResult` with balances on every path.
- [x] **Every best-in-class sub-option** — contribute/donate/deposit + grant/disburse/payout aliases;
      view balance; the collective-pool niche is fully covered.
- [x] **Failure modes honest** — insufficient user funds / underfunded pool fail with the available
      amount quoted; never silently succeed.
- [x] **Idempotent / re-runnable** — each invocation reruns the whole workflow; no duplicate-special-case.

### B. Reachability & UI
- [x] **A command panel exists** — `!treasury` → Treasury panel (pool + viewer wallet; ➕ Contribute
      modal, 🔄 Refresh).
- [x] **Reachable every natural way** — `!treasury` group + `build_help_menu_view` hook + Economy-hub
      Treasury button (`economy:treasury`).
- [N/A] **Integrated into Setup** — no onboarding config (collective pool, no per-guild knobs).
- [x] **Return navigation** — Treasury view inherits HubView nav; Economy path attaches back-to-economy.
- [x] **In-place, not spammy** — Contribute/Refresh re-read + redraw the panel in place (`safe_edit`).

### C. Convenience
- [x] **Low-step** — one command/modal per action; non-positive amounts rejected before any I/O.
- [x] **Defaults** — no presets needed; modal is free-amount.
- [x] **Clear feedback** — every action shows exact pool + wallet balances with emoji; failures quote the
      available amount.

### D. Authority & safety
- [x] **Authority re-checked at callback** — disburse is `@has_permissions(manage_guild=True)`; there is
      **no view-side disburse button**, so a member panel can never move server coins out (contribute is
      open by design — you spend your own coins).
- [x] **All writes through the audited seam** — coin legs via `economy_service.debit_in_txn`/
      `credit_in_txn` (reason `treasury:contribute`/`treasury:disburse`, actor recorded) →
      `economy_audit_log`; `EVT_BALANCE_CHANGED` emitted **after commit**; pool row is domain inventory.
- [N/A] **Provisioning pipeline** — no resource creation.
- [x] **Reuses governance** — `manage_guild` floor on disburse; no second allowlist.

### E. Configuration
- [N/A] **Settings pipeline** — no settings keys / widgets by design (a collective resource has no
      per-guild tunables); registry `has_cleanup_rules: False` correct.
- [N/A] **config-input widgets** — none.
- [N/A] **Everything configurable that should be** — nothing should be configurable here.

### F. Wiring & discoverability
- [x] **Registry** — key `treasury`, `category: economy`, `parent_hub: economy`, entry `treasury`,
      soft-dep economy, capabilities `treasury.pool.view/contribute/disburse`.
- [x] **Discoverable in Help** — `build_help_menu_view` hook; Economy-hub primary child; loaded in
      `config.py` INITIAL_EXTENSIONS.

### G. Tests & evidence (required for ✔)
- [x] **Behavior tests** — `test_treasury_service.py` (10 cases): both legs on one conn + emit-after-
      commit, insufficient-funds rollback (no emit), underfunded pool writes nothing, non-positive
      rejected before I/O.
- [x] **Authority tests** — disburse records the manager as actor (service test); the `manage_guild`
      gate at the command is now pinned by `test_treasury_cog.py` (denied without / allowed with /
      owner-bypass) — punch #1 CLEARED.
- [x] **Mutation-seam tests** — emit-only-after-commit + no-op-on-exception pinned in the service tests.
- [x] **View tests** — `test_economy_treasury_button.py` (3 cases): button present, edits in place,
      attaches back-to-economy; plus `test_treasury_contribute_modal.py` (Contribute-modal parse edge
      cases) — punch #2 CLEARED.
- [ ] **Live walkthrough recorded** — pending → punch #5.
- [ ] **Owner ✔** — pending → punch #6.

## Punch-list (clear these to certify)
1. **✅ DONE 2026-07-01 (dispatch run) — Cog-level command tests.** `tests/unit/cogs/test_treasury_cog.py`
   (13 cases) exercises `!treasury` (panel open), `contribute` (calls service / rejects non-positive), and
   `grant` (disburse + mention-on-success, rejects non-positive, and the `manage_guild`/owner authority
   gate — denied without, allowed with, owner-bypass).
2. **✅ DONE 2026-07-01 (dispatch run) — Modal-parse tests.**
   `tests/unit/views/test_treasury_contribute_modal.py` (6 cases) covers `_ContributeModal.on_submit`:
   non-int / empty / negative / zero → ephemeral error + no write; valid (incl. large + whitespace) →
   `treasury_service.contribute` + in-place redraw.
3. **Document the economy soft-dependency** *(owner, minor)* — record + test the "panel opens read-only
   when economy is disabled" fallback.
4. **Help-actionability note** *(offline, minor)* — note that economy children aren't subject to the
   Games-hub actionability contract (no treasury Help-nav pin today).
5. **Live walkthrough** *(owner / live-bot)* — `/verify-bot` boot + contribute then grant, confirm
   balances + audit rows, with screenshots.
6. **Owner sign-off** — maintainer confirms "it does its job the most convenient way."

## Evidence
- **Tests:** `tests/unit/services/test_treasury_service.py` (10 cases) ·
  `tests/unit/views/test_economy_treasury_button.py` (3 cases)
- **Walkthrough:** pending (punch #5)
- **Owner sign-off:** pending (punch #6)

## Verdict
Treasury is **functionally complete and money-safe** — a transactional server-owned coin pool (both legs
one connection, emit-after-commit, never mints, audited coin trail), correctly gated (`manage_guild` on
disburse, no member-reachable disburse), and reachable via command/Help/Economy-hub with in-place
navigation. It is **not yet `✔ certified`**: the gaps are **cosmetic test coverage** (#1/#2/#4), a
soft-dependency doc/test (#3), and the owner walkthrough/sign-off (#5/#6). No safety/audit/dead-end issues
found.
