# SuperBot — Mutation Boundary Audit

> **Status:** `audit` — living inventory. Run against the codebase after the
> Service Ownership Hardening session (2026-05-24). Update this document
> when new mutation paths are introduced or existing paths change.
>
> **Authority:** `docs/ownership.md` is the binding ownership contract.
> This document records audit findings against that contract — it does not
> define new rules.

---

## Summary

| Status | Count | Domains |
|---|---|---|
| `correct` | 9 | Economy, XP, Governance, Moderation, Settings, Bindings, Resources, Setup apply path, Game state |
| `missing side effect` | 1 | Setup session lifecycle — **fixed in this session** |
| `documented exception` | 5 | Inventory, Counting, Chain, Mining, Deathmatch |
| `violation` | 0 | — |

**No blocking violations found.** The one `missing side effect` gap (setup_session
audit emission) was closed in the same session as this audit.

---

## Status definitions

| Status | Meaning |
|---|---|
| `correct` | Routes through declared owner with all required side effects (validate → write → audit → cache → event) |
| `missing side effect` | Correct owner is used, but audit / cache / event / rollback behavior is incomplete |
| `documented exception` | Direct write path is explicitly allowed and documented in `docs/ownership.md` |
| `legacy tolerated` | Imperfect but low-risk and not worth fixing yet; tracked separately |
| `violation` | Writes through the wrong layer — must be fixed before next feature PR |

## Risk levels

| Risk | Criteria |
|---|---|
| P0 | Can corrupt money, XP, moderation records, governance permissions, or production startup/shutdown safety |
| P1 | Can create inconsistent guild configuration or stale caches |
| P2 | Can create confusing UX, duplicate behavior, or incomplete diagnostics |
| P3 | Cleanup / observability only — no correctness impact |

---

## Audit table

| Domain | Caller | Mutation | Current path | Correct owner | Required side effects | Status | Risk | Fix applied |
|---|---|---|---|---|---|---|---|---|
| Economy — credit | cogs, views, setup pipeline | coin credit | `economy_service.credit()` | `services/economy_service.py` | `economy_audit_log` row + `economy.balance_changed` | `correct` | — | — |
| Economy — debit | cogs, views, setup pipeline | coin debit | `economy_service.debit()` | `services/economy_service.py` | `economy_audit_log` row + `economy.balance_changed` | `correct` | — | — |
| Economy — transfer | economy cog, views | peer transfer | `economy_service.transfer()` | `services/economy_service.py` | two `economy_audit_log` rows + event | `correct` | — | — |
| Economy — bet/settle | game views (BJ, RPS) | game payout | `economy_service.bet_and_settle()` | `services/economy_service.py` | `economy_audit_log` rows + event | `correct` | — | — |
| XP — award | cogs, listeners, work view | XP grant | `xp_service.award()` | `services/xp_service.py` | `xp.awarded` + `xp.level_up` events | `correct` | — | — |
| XP — reset | admin cog | XP reset | `xp_service.reset()` | `services/xp_service.py` | `xp.reset` event | `correct` | — | — |
| Governance — visibility | governance cog, admin views, setup pipeline | subsystem visibility | `GovernanceMutationPipeline.set_visibility()` | `governance/writes.py` | `governance_audit_log` + events + cache invalidate | `correct` | — | — |
| Governance — cleanup policy | governance cog, setup pipeline | cleanup policy | `GovernanceMutationPipeline.set_cleanup_policy_for_scope()` | `governance/writes.py` | `governance_audit_log` + events + cache invalidate | `correct` | — | — |
| Governance — internal bypass audit | `governance/execution.py` | bypass audit row only | `_audit_internal_bypass()` (carve-out) | `governance/writes.py` (carve-out) | append-only row, no events | `documented exception` | — | — |
| Moderation — warn | mod cog, views | warning record | `moderation_service.warn()` | `services/moderation_service.py` | `mod_logs` row + `moderation.action_taken` | `correct` | — | — |
| Moderation — timeout/kick/ban/unban | mod cog, views | Discord action + record | `moderation_service.timeout()` / `.kick()` / `.ban()` / `.unban()` | `services/moderation_service.py` | `mod_logs` row + Discord API call + `moderation.action_taken` | `correct` | — | — |
| Moderation — clear warnings | mod cog, admin views | warning bulk clear | `moderation_service.clear_warnings()` | `services/moderation_service.py` | `mod_logs` row + `moderation.action_taken` | `correct` | — | — |
| Settings — set value | setup pipeline, settings cog/views | guild setting write | `SettingsMutationPipeline.set_value()` | `services/settings_mutation.py` | `settings_audit` row + `audit.action_recorded` + cache invalidate | `correct` | — | — |
| Bindings — set binding | setup pipeline, binding views | channel/role binding | `BindingMutationPipeline.set_binding()` | `services/binding_mutation.py` | `binding_audit_log` row + `audit.action_recorded` + cache invalidate | `correct` | — | — |
| Bindings — clear binding | setup pipeline | binding removal | `BindingMutationPipeline.clear_binding()` | `services/binding_mutation.py` | `binding_audit_log` row + `audit.action_recorded` + cache invalidate | `correct` | — | — |
| Resources — provision | setup pipeline | channel/role/category creation | `ResourceProvisioningPipeline.provision(confirmed=True)` | `services/resource_provisioning.py` | `resource_provisioning_audit` row + `EVT_RESOURCE_PROVISIONED` | `correct` | — | — |
| Setup apply path | final review view | staged operation apply | `setup_operations.apply_operations()` dispatcher → domain pipelines | setup is orchestrator; domain pipelines own writes | depends on operation kind (each routes correctly) | `correct` | — | — |
| Game state — checkpoints | game cogs, game views | in-flight game state | `game_state_service.save()` / `.clear()` | `services/game_state_service.py` | none (audit-free by design — ADR-002) | `correct` | — | — |
| Game state — balance settlements | game views (BJ, RPS, proof_channel) | coin delta on game outcome | `economy_service.credit()` / `.debit()` / `.bet_and_settle()` | `services/economy_service.py` | full economy side effects | `correct` | — | — |
| Setup session — start | setup cog, launcher | `setup_session` row upsert | `setup_session.start_session()` → `utils/db/setup_session.*` | `services/setup_session.py` | **was missing `audit.action_recorded`** | `missing side effect` → **fixed** | P3 | Added `audit.action_recorded` emission (best-effort) |
| Setup session — complete | final review view | status → "complete" | `setup_session.mark_complete()` → `utils/db/setup_session.*` | `services/setup_session.py` | **was missing `audit.action_recorded`** | `missing side effect` → **fixed** | P3 | Added `audit.action_recorded` emission (best-effort) |
| Setup session — dismiss | launcher view | status → "dismissed" | `setup_session.dismiss()` → `utils/db/setup_session.*` | `services/setup_session.py` | **was missing `audit.action_recorded`** | `missing side effect` → **fixed** | P3 | Added `audit.action_recorded` emission (best-effort) |
| Inventory | inventory cog | inventory CRUD | `utils/db/inventory.*` direct | `utils/db/inventory.py` | none | `documented exception` | — | Intentional — single-subsystem CRUD |
| Counting | counting cog | counting state | `utils/db/games/counting.*` direct | `utils/db/games/counting.py` | none | `documented exception` | — | Intentional — single-subsystem CRUD |
| Chain | chain cog | chain channel state | `utils/db/games/chain.*` direct | `utils/db/games/chain.py` | none | `documented exception` | — | Intentional — single-subsystem CRUD |
| Mining | mining cog | mining inventory | `utils/db/games/mining.*` direct | `utils/db/games/mining.py` | none | `documented exception` | — | Intentional — single-subsystem CRUD |
| Deathmatch | deathmatch cog | deathmatch stats | `utils/db/games/deathmatch.*` direct | `utils/db/games/deathmatch.py` | none | `documented exception` | — | Intentional — single-subsystem CRUD |

---

## Domain notes

### Economy

INV-F (AST test in `tests/unit/invariants/`) enforces that `db.add_coins` and
`db.set_coins` appear only inside `services/economy_service.py` and
`utils/db/economy.py`. All game views confirmed to use `economy_service` for
balance mutations — no direct balance writes found in views or cogs.

### XP

INV-G (AST test) enforces no `db.add_xp` / `db.delete_xp` outside the service
and its DB module. Level recalculation is bundled inside `xp_service.award()`.

### Governance

INV-E (`test_apply_template_uses_pipeline`) enforces pipeline use for visibility
and cleanup writes. The `_audit_internal_bypass` carve-out is fully documented
in `docs/ownership.md` including why it is not routed through the pipeline.

### Setup session

`setup_session.py` is not a domain mutation pipeline — it manages wizard
lifecycle state (`pending` / `in_progress` / `complete` / `dismissed`). Its DB
path (`utils/db/setup_session`) is correct. The missing side effect was that
lifecycle transitions did not emit `audit.action_recorded`, so setup session
activity was invisible to the audit channel subscriber.

**Fix applied:** `start_session`, `mark_complete`, and `dismiss` now emit
`audit.action_recorded` via `services/audit_events.emit_audit_action()`.
Emission is best-effort (failure is logged at WARNING and swallowed) because
the DB transition is authoritative and a dropped audit event is non-fatal.
`mutation_type` tokens: `"setup.session.started"`, `"setup.session.completed"`,
`"setup.session.dismissed"`.

### Inventory / Counting / Chain / Mining / Deathmatch

These subsystems use direct `utils/db/games/*.py` calls. This is explicitly
documented in `docs/ownership.md`'s subsystem ownership table and is intentional:
- Single-subsystem state — no cross-subsystem impact.
- Simple CRUD — no audit, event, or cache requirements at this time.
- Adding a full mutation pipeline would be an architecture change requiring a
  doc-first proposal, not a hardening fix.

### Game state (blackjack, RPS)

Two-layer ownership: coin mutations go through `economy_service` (correct);
game progress checkpoints go through `game_state_service` (correct). The
`_persistence.py` helpers inside cog packages are thin wrappers that call
`game_state_service` — they do not bypass it.

---

## Known future work (not in scope of this session)

These are tracked in `docs/health/platform-consistency-ledger.md` and the
phase-2 PR sequence, not in this audit.

- `setup_session.mark_in_progress()` — does not emit audit. Low value
  (in-progress is transient state); revisit if setup observability is requested.
- `tournament_state_service.py` — audit-free by design (same rationale as
  `game_state_service`; ADR-002).
- Inventory/counting/chain/mining/deathmatch direct-db paths — correct as
  documented; promote to service layer only when cross-subsystem mutation
  or auditability becomes a real requirement.
