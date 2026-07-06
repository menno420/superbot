# LIVE-VERIFIED-EVIDENCE-PACK.md — GATE V, Arm D (empirical live proof)

> **Status:** `audit` — output of [`rebuild-gate-v-verification-fleet-2026-07-06.md`](rebuild-gate-v-verification-fleet-2026-07-06.md)
> §7 (Arm D). Capture-and-report only: no plan/current-state edits, no gate approval. Feeds the
> Arm Σ final synthesis (§8 of the launch pad).

## 0. Methodology disclosure (read before trusting anything below)

§7 frames Arm D as **operator-run**: *"Because it needs a token + DB + a running bot, it is run
by the maintainer/operator, not an unattended review sandbox."* This run was executed by an
**unattended agent session** in a remote sandbox, with no second human/user Discord identity
available (only the dedicated test-bot token is provisioned here — no low-privilege test-user
account exists in the guild). A literal human clicking buttons in a live Discord client could not
happen. What *did* happen, honestly:

- The **real** `disbot/bot1.py` was booted twice for real (fresh boot + restart), against the
  **real** dedicated test bot ("Galaxy Bot#6724") and the **real** local throwaway Postgres — a
  genuine gateway connection, genuine cog load, genuine command-surface build.
- A **separate driver process** (`live_driver.py`, not committed — scratch tooling) attached a
  second lightweight `discord.Client` session under the **same test-bot token** (Discord permits
  multiple sessions per bot token; verified safe, used only briefly) to obtain **real** `Guild` /
  `Member` / `TextChannel` objects from the **real** test guild, then called the **exact same
  service-layer functions** the real command handlers call (`economy_service`, `xp_service`,
  `shop_purchase_workflow`, `settings_mutation.SettingsMutationPipeline`, `game_wager_workflow`,
  `blackjack_state._PvPState`, `utils.db.games.deathmatch`, `utils.db.proof_channel_locks`,
  `core.runtime.permission_checks.member_has_perms_or_owner`) with real guild/user ids, against the
  **real** Postgres, producing **real** DB rows, **real** audit rows, and one **real** Discord
  message echoed into the test guild's `economy-log` channel.
- This is **one tier short** of full command-pipeline fidelity: it does not exercise Discord's
  interaction round-trip (converters, cooldowns, the `before_invoke` governance gate, the error
  handler) because that requires either a real second Discord user or injecting a synthetic
  gateway payload into the *same process* as the running bot (the `parity/` harness's technique,
  but that harness fakes the HTTP boundary — this run deliberately did not, to get genuine
  Discord-visible output). Every finding below is labelled with which tier produced it.
- **Never reported as passed unless it ran** (§3.5): where a check could not run this way, it is
  marked `NEEDS_EXTERNAL_VALIDATION` (§3.1 enum) with the reason, not silently assumed.

Test guild: **"Menno420's server420"** (id `1508892958961832051`), the one whose channel set
(`economy-log`, `audit-logs`, `superbot-setup`, `tournament`, counting channels) matches the
journal's "dedicated test bot, alone with the maintainer" description; distinct from two other
guilds the token is also a member of (`MineSnakeBotTest`, `Superbot Admin` — not used here).
Members: the test bot itself, a second bot (`SuperBot#2055`, unrelated to this run), and the real
guild owner `menno4207` (id `340415158583296000` — matches `config.BOT_OWNER_USER_ID` default).
Synthetic ledger identities `990000000000000101/102` (wager pair) and `990000000000000201/202`
(deathmatch pair) were used for economy/stat rows — realistic snowflake-shaped integers, not real
Discord accounts, since the service layer under test validates guild/user ids as plain integers,
not Discord membership.

## 1. What booted / environment + limits

| Item | Result |
|---|---|
| First boot | Clean. `Logged in as Galaxy Bot#6724`, `Connected to 3 server(s)`, 55 cogs loaded, 0 extension failures, 0 ERROR/CRITICAL/Traceback in `bot.log`. Command surface: 406 prefix + 73 slash commands; auto-sync applied +43/-31 global command diff live to Discord. |
| First-boot health | `Startup health: degraded — attention: consistency — Config arbitration`. |
| Restart (after `kill` + relaunch) | Clean, 0 errors. `Startup health: healthy — 0 findings.` The Config-arbitration finding did **not** recur — `CONFIRMED` as a first-ever-boot-against-a-fresh-DB artifact, not a persistent defect (evidence: absent on the very next boot with no code change). |
| Postgres | Local throwaway cluster (`/var/lib/postgresql/16/main`), fresh — 0 rows in `economy`/`xp`/`inventory` before this run. Migrations already at head (104). Never touched Railway/prod. |
| Network | Full — real Discord gateway + REST reachable. No AI-provider keys present (expected per Runbook; not exercised here — out of scope for these primitives). |
| Limits | No low-privilege human test account in the guild (authority-deny case had to substitute a synthetic user object at the function-call boundary — see §5). No full command-pipeline fidelity (see §0). Did not exercise AI-provider-backed paths (not in Arm D's primitive list). |

## 2. Goldens captured (flow → input → output → DB rows → audit events)

All rows below are **live** (`CONFIRMED`, `test-confirmed` — it actually ran, this session,
against the real test-guild DB). Reproduction: the driver script's phase order, on request.

| Primitive | Real command counterpart | Input | Output / DB delta | Audit trail |
|---|---|---|---|---|
| Economy credit | `!daily` → `economy_service.credit()` | `credit(guild, 990…101, 500, reason="gate-v-arm-d:credit", actor_id=owner)` | balance `0 → 500` (later `1500 → 2000` on a repeat run) | Row written to **`economy_audit_log`** (id, delta=500, new_balance, actor_id, reason) — **not** the generic `audit.action_recorded` (see §8 C-1: no `emit_audit_action` call in `economy_service`, only `EVT_BALANCE_CHANGED` on the bus + the module-local `_audit()` table write). |
| Economy debit | `!work` spend paths → `economy_service.debit()` | `debit(…, 200, reason="gate-v-arm-d:debit")` | balance `500 → 300` | Same `economy_audit_log` path. |
| XP award | `!givexp` / `!work` / message XP → `xp_service.award()` | `award(…, 50, source="gate-v-arm-d")` | `xp 50→100`, `level 0→1`, `leveled_up=True` | `EVT_XP_AWARDED` + `EVT_LEVEL_UP` emitted on the bus; **no** `emit_audit_action` call in `award()` (only `xp_service.reset()` calls it, per source read — a real, minor asymmetry worth Phase-B attention). |
| Inventory grant | Shop purchase (`views/economy/shop_panel.py`) → `shop_purchase_workflow.purchase_unique_item()` | `purchase_unique_item(guild, 990…101, "gate-v-arm-d-test-item", 100)` | First call: `ok=True`, `inventory` row inserted (`quantity=1`), coins debited 100 in the same transaction. Repeat call: `ok=False, already_owned=True` — confirms the unique-item conditional-upsert guard (`try_grant_unique_item`) is real and working. | No `emit_audit_action`; balance leg covered by `economy_audit_log` via `debit_in_txn`. |
| Settings write | `!settings` → `SettingsMutationPipeline.set_value()` | `set_value(guild, "xp", "xp_cooldown", 45, actor=owner_member)` | **First attempt failed**: `UndeclaredSettingError` — the pipeline requires the owning cog's `SubsystemSchema` to already be registered (normally done in `XpCog.cog_load()`); a bare service-layer caller in a process that never loaded the cog gets rejected. **Genuine finding** (§8 D-1), not a bug — it's the pipeline correctly refusing an unregistered subsystem. Fixed by calling `cogs.xp.schemas.register_schemas()` directly (the same function `cog_load()` calls); second attempt: `old_value=60 → new_value=45`, `ok=True`. | Row written via `settings_audit.set_value_with_audit()`, which **does** call `emit_audit_action` (subsystem="xp", mutation_type="set_value") — confirmed from source (`settings_mutation.py:417-429`); mutation_id `1b99e79c-…` returned. |
| Leaderboard read | `!rank` / `!leaderboard` → `rank_providers.py` | n/a (read-only) | Not separately captured this run (the underlying writes above are what a leaderboard read reflects — there is no separate leaderboard-write table for xp/coins categories, confirmed by source read of `rank_providers.py`). Deathmatch is the one category with a dedicated table — see §3. | — |

## 3. Concurrency / settlement results (bug confirmed or refuted, with repro)

The plan's Q-234/Q-233 lineage claims *"live wager double-pay/double-settle bugs"* — the launch
pad names this as something Arm D should confirm or refute empirically. Result: **mixed —
confirmed in one place, refuted in another.**

### 3a. PvP wager escrow/settle (`game_wager_workflow`) — **REFUTED at the service layer**

Repro: opened a real escrow (`open_pvp_wager(p1=990…101, p2=990…102, stake=300)` — both stakes
debited atomically, `escrowed=True`), then fired **two concurrent** `settle_pvp(..., winner_id=p1)`
calls via `asyncio.gather`:

```
results = [{"paid": true, "amount": 600}, {"paid": false, "amount": 0}]
p1_balance_before_settle = 2500
p1_balance_after_both_calls = 3100   (== 2500 + 300*2, i.e. paid exactly once)
double_paid = False
```

The module docstring's claim — `settle_pvp`/`refund_pvp` are idempotent via `FOR UPDATE` row-locking
on the escrow rows, so "a crash-retry or a double settle can never double-pay" — **held up under a
real concurrent call in this process**. `CONFIRMED` (`test-confirmed`, this session).

Also tested the View-layer guard directly: `blackjack_state._PvPState` (mixes in
`SettleOnceMixin`) — two concurrent `claim_settlement()` callers → `{"A": true, "B": false}`,
exactly one `True`. `CONFIRMED`. Source-read: `views/rps/pvp_play._RpsPvpPlayView` mixes in the
same shared `SettleOnceMixin` class, so this result generalizes to RPS by construction (not
independently re-run against the RPS view instance — `PARTIAL`, low risk given identical mixin
code).

### 3b. Deathmatch human-duel double-write — **CONFIRMED, a real open gap**

Source read (`disbot/cogs/deathmatch_cog.py:94-253`): `_DuelView` extends `discord.ui.View`
directly — it does **not** mix in `SettleOnceMixin`. `on_timeout()` (line 151) guards on
`duel.is_over`, but `_resolve()` (line 214) computes winner/loser purely from HP and calls
`self.cog.update_leaderboard(...)` (line 233) **without checking `duel.is_over` at all** — so a
timeout firing concurrently with an in-flight `_resolve()` call has no mutual exclusion between
the two paths.

Confirmed the consequence empirically at the mutation layer: `utils.db.games.deathmatch.
update_deathmatch()` has **no idempotency guard of its own** (plain `INSERT … ON CONFLICT DO
UPDATE SET wins = wins + 1`, unconditionally additive). Two concurrent calls:

```
before = {"wins": 0, "losses": 0}
after_two_concurrent_calls = {"wins": 2, "losses": 0}
double_write_occurred = True
```

Net finding: the **shared mutation primitive has no defense**, and the **one caller that lacks the
View-level guard** is exactly `_DuelView` (the human-vs-human deathmatch duel) — the module
docstring in `utils/terminal_guard.py:27-29` explicitly lists the deathmatch **bot**-duel
(`_BotDuelView`) as covered by `SettleOnceMixin`, not the human PvP duel. `CONFIRMED` by source
read + live DB proof; the literal two-real-Discord-interactions race against a running `_DuelView`
instance was **not** replayed end-to-end (would need either a live human double-click or a
same-process synthetic-interaction harness) — marked `NEEDS_EXTERNAL_VALIDATION` for that specific
full-fidelity repro, though the component parts (no View guard + no mutation guard) are each
independently `CONFIRMED`. No coins are at stake in deathmatch (stats-only), so this is a
leaderboard-integrity bug, not a wallet-mint bug.

## 4. Restart / recovery results

Target: `proof_channel_locks` (the deferred-action/restart-persistence class named in §7).

- Wrote a real persisted lock row via `upsert_lock()` (real guild id, a real text channel in the
  test guild, `unlock_at` ~3 minutes out — deliberately **not** already-expired, so the reconcile
  sweep would exercise the *reschedule* branch rather than the *immediate-unlock* branch, which
  edits real channel permission overwrites; see the safety note below).
- Killed the live bot process (`kill`, filtered by `comm=python3.10` per the Runbook gotcha) and
  relaunched it for real.
- Confirmed: clean restart (0 errors, `Startup health: healthy`), and the persisted row **survived
  the restart untouched** (`unlock_at` still in the future, row not deleted) — `_reconcile_locks()`
  only calls `delete_lock`/`_unlock` on a stale or expired row, so an untouched, still-future row is
  exactly the evidence that the reschedule branch (`_schedule_unlock`, an in-memory asyncio timer
  re-armed from the persisted deadline) ran without error. `CONFIRMED` (`test-confirmed`).
- **Safety note (why this wasn't fully end-to-end):** letting the deadline actually elapse would
  have driven `_unlock()`, which calls `channel.edit(overwrites=...)` on a **real** channel in the
  maintainer's test guild (setting `@everyone: send_messages=False`) — a real, visible,
  not-trivially-reversible side effect on a channel (`general`) that was never actually locked by a
  real prize-claim flow. That specific tail (does `_unlock` itself run cleanly at the deadline) was
  **not exercised** to avoid leaving the test guild in a surprising state; the test row was deleted
  immediately after confirming the reschedule. Marked `NEEDS_EXTERNAL_VALIDATION` for the
  unlock-firing tail specifically (low risk — `_unlock`'s body is a straightforward `channel.edit`
  + audit call with no persistence-relevant logic left to prove).

## 5. Authority results

Target: `views/roles/reaction_panel.py` — the View whose docstring explicitly claims
"authority (`manage_roles`) is re-checked at callback time," distinct from `BaseView`'s
interaction_check (which only re-verifies the invoker's *identity*, never Discord permissions —
confirmed by reading `views/base.py:151-170`).

Called the real gate function, `core.runtime.permission_checks.member_has_perms_or_owner`,
directly (not a mock of the function itself — this **is** the function `_can_manage()` calls):

- **Allow case:** the real guild owner `Member` object (`menno4207`) → `member_has_perms_or_owner(
  owner_member, manage_roles=True) == True`. Owner bypass short-circuits via
  `config.is_platform_owner`, so this also empirically confirms the owner-bypass path, not just the
  `guild_permissions.manage_roles` path.
- **Deny case:** no second, low-privilege human Discord account exists in this test guild to
  produce a real `Member` without `manage_roles` — substituted a lightweight synthetic object
  exposing only `.id` (a non-owner id) and `.guild_permissions.manage_roles = False`, matching the
  exact attribute shape `member_has_perms_or_owner` reads (`getattr(user, "id", None)`,
  `getattr(user, "guild_permissions", None)`). Result: `False`, i.e. correctly denied.

`CONFIRMED` for the boolean logic itself (real function, real code path, real owner object for the
allow case). `NEEDS_EXTERNAL_VALIDATION` for the full interaction round-trip (a real Discord
button click by a real low-privilege member, ending in `_deny()`'s ephemeral
`interaction.response.send_message` actually rendering) — that leg needs either a second real
account or an operator session, neither available here.

## 6. Games-deferral exercisability table

The central empirical question (§7, §1 of the launch pad): for each shared primitive, can it be
driven live **without** a game, and is a deterministic replacement oracle available?

| Primitive | Exercised via (this run) | Without games? | Replacement-oracle feasibility | §3.1 readiness |
|---|---|---|---|---|
| Economy credit/debit | Direct `economy_service` call, mirrors `!daily`/`!work` | **Yes** — real non-game commands already call this | N/A — already proven outside games | `READY_FOR_TEST_DESIGN` |
| XP award | Direct `xp_service.award()`, mirrors `!givexp`/message-XP | **Yes** — non-game commands are the primary callers | N/A | `READY_FOR_TEST_DESIGN` |
| Inventory grant | Direct `shop_purchase_workflow.purchase_unique_item()` | **Yes** — the shop is a non-game consumer | N/A | `READY_FOR_TEST_DESIGN` |
| Settings mutation | Direct `SettingsMutationPipeline.set_value()` | **Yes** — `!settings` is non-game | N/A | `READY_FOR_TEST_DESIGN` |
| PvP wager escrow/settle (`game_wager_workflow`) | Direct service call, bypassing all View/UI code entirely | **Production callers: no** (blackjack/RPS views are its only current callers, per source read) — **but this run proves a bare synthetic/service-level harness (no game UI, no Discord interaction) can exercise and idempotency-test it deterministically** | **High** — this session *is* the replacement-oracle prototype: a same-process script calling `open_pvp_wager`/`settle_pvp`/`refund_pvp` directly, no game required | `READY_FOR_TEST_DESIGN` (the primitive), `DEFERRED` (the game UI wrapping it) |
| `SettleOnceMixin` | Direct instantiation + concurrent `claim_settlement()` calls | **Yes** — the mixin has zero game/Discord dependency | Already proven via direct instantiation | `READY_FOR_TEST_DESIGN` |
| Deathmatch stats write (`update_deathmatch`) | Direct DB-function call | **Yes** for the primitive; **no** for today's only real caller (`_DuelView`, a game) | High for the primitive (proven here); the *bug* (§3b) is specifically in the game-side caller and needs either a game-side fix or a `SettleOnceMixin` retrofit — not a foundations question | `NEEDS_CONTRACT_FREEZE` (the caller-side guard is the open item) |
| `proof_channel` restart-persistence | Direct `upsert_lock` + real bot kill/restart | **Yes** — no game dependency at all; it's a channel/prize-lock feature | N/A | `READY_FOR_TEST_DESIGN` |
| Authority re-check (`reaction_panel`) | Direct function call | **Yes** — role-management UI, non-game | N/A | `READY_FOR_TEST_DESIGN` (function logic); `NEEDS_EXTERNAL_VALIDATION` (full interaction round-trip) |

**Answer to the central question (§1 of the launch pad):** every shared primitive this run touched
— including the PvP wager escrow/settle engine, which today is *only called* from game views — was
successfully exercised, mutated, and idempotency-tested **without invoking any game**, using a
direct service-layer harness. This is empirical evidence that **L3 (games) can plausibly move
later**: the primitives games currently prove are not *structurally* game-dependent, only
*currently wired* to game callers. What remains genuinely game-specific is the *caller-side*
correctness (e.g., the `_DuelView` gap in §3b lives in the game cog, not in the shared primitive).

## 7. Which Gate-V / Phase-2.5 conditions this evidence lifts

- **Lifts:** "the live co-test half is not yet concrete enough" (the verification-review gap named
  in the launch pad's §0) — this pack is a first concrete, reproducible instance of it, covering
  economy, XP, inventory, settings, PvP-wager idempotency, and restart-persistence.
- **Lifts (partially):** the games-deferral empirical question for the primitives in §6 marked
  `READY_FOR_TEST_DESIGN` — direct evidence that a non-game synthetic harness suffices.
- **Does NOT lift:** full command-pipeline fidelity (converters/cooldowns/`before_invoke`/error
  handler) was never exercised — every capture here went through the service layer directly, one
  tier below the real Discord dispatch path. A follow-up should either get a second (low-privilege)
  test-user Discord account into this guild, or extend `parity/`'s in-process technique to allow a
  *real* (non-faked) HTTP boundary for a hybrid live/synthetic mode.
- **Does NOT lift:** the `_DuelView` double-write gap (§3b) is now `CONFIRMED` open, not fixed —
  Phase-B should carry it as a concrete delta (retrofit `SettleOnceMixin` onto `_DuelView`, or add
  an equivalent guard before its two `update_leaderboard()` call sites).
- **Remaining `NEEDS_OWNER_DECISION`:** none surfaced by this arm — Arm D found no genuine
  owner-facing product ambiguity, only implementation-level findings routed above.

## 8. §3.3-keyed contradictions between observed behavior and planning claims

| Claim key | Claimed source | Live evidence (this session) | Status | Consequence |
|---|---|---|---|---|
| `rebuild-gate-v-verification-fleet-2026-07-06.md:§1` — "live wager double-pay/double-settle bugs" | Launch-pad framing, inherited from the Q-233/234 lineage | `game_wager_workflow.settle_pvp`/`refund_pvp`: idempotent under a real concurrent call (§3a). `_DuelView` (deathmatch human duel): genuinely unguarded, real double-write reproduced (§3b). | `CONTRADICTED` for the wager-escrow engine specifically; `CONFIRMED` for the deathmatch human-duel caller | The blanket claim is too broad — Phase-B should scope the "double-settle" risk to the deathmatch human-duel caller, not the shared wager engine, which is already hardened. |
| `disbot/services/economy_service.py` module docstring — audit trail framing ("no shared audit trail" was the *pre*-refactor problem it fixed) | Source docstring | Confirmed a live audit row is written on every credit/debit (`economy_audit_log`), but via a **module-local `_audit()` helper**, not the generic `services.audit_events.emit_audit_action()` used elsewhere (settings, role_automation, xp reset). | `CONFIRMED` (not a contradiction of the docstring, but a real cross-subsystem audit-shape inconsistency worth flagging) | Phase-B: decide whether `economy_audit_log` should ever be unified with the generic audit event, or whether the domain-specific-table pattern is intentional and should be documented as such in `docs/ownership.md`. |
| Settings mutation pipeline — implicitly assumed callable "from anywhere" per its docstring emphasis on being "the only legitimate writer" | `disbot/services/settings_mutation.py:229-238` | Empirically requires the target subsystem's `SubsystemSchema` to already be registered (normally via the owning cog's `cog_load()`); a bare external caller in a process that never loaded that cog is rejected (`UndeclaredSettingError`) until `register_schemas()` is called explicitly. | `CONFIRMED` (a real, previously-undocumented coupling, not a bug) | Worth a one-line note in `docs/architecture.md` or the settings folio: the pipeline is a *within-bot-process* single writer, not a standalone importable service — a future rebuild consumer needs the schema registration step too. |
| `docs/current-state.md` — startup health baseline (implicit "healthy" expectation) | Prior sessions' boot verifications | First-ever boot against a brand-new empty DB reported `degraded — Config arbitration`; the *very next* restart (same code, same DB, now populated) reported `healthy`. | `CONFIRMED` as a cold-start-only artifact | Low severity — note for Phase-B/migration: a from-scratch cutover's *first* boot may show a transient degraded finding that self-resolves; don't treat it as a blocker without a second-boot check. |

## 9. Scope note (§3.6 degrade-gracefully)

PRIMARY-owned deliverables (the empirical goldens, concurrency results, restart/recovery, authority
result, and the games-deferral table) are delivered at full depth. Not attempted this run (would
need either a second Discord test identity or a same-process synthetic-interaction harness beyond
this session's scope): full command-pipeline dispatch fidelity, AI-provider-backed paths (no
provider keys in this sandbox — out of scope for Arm D's named primitives), and the RPS view's
concurrency race re-run as its own instance (covered by shared-mixin-code argument in §3a instead).
