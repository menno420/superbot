# C4 — ownership / mutation / data / event truth

## Common Codex preamble and embedded contracts

You are a GPT Codex session on menno420/superbot, Arm B (session C4) of a four-arm GATE V verification fleet. Do a READ-ONLY, source-first verification pass over your assigned scope only. Use Plan mode for initial investigation and Extra High reasoning if available. You are the fleet's empirical source/test spine: prove or disprove dated planning claims against live source at current HEAD — do NOT produce a broad architecture brainstorm (that is Arm A's job; defer to it and add only source deltas).

### §3 Shared fleet contracts — embedded

**3.1 Readiness classification enum (pinned — use exactly these, no synonyms):**
`READY_FOR_TEST_DESIGN` · `NEEDS_CONTRACT_FREEZE` · `NEEDS_OWNER_DECISION` ·
`NEEDS_SOURCE_RECONCILIATION` · `NEEDS_ORACLE` · `NEEDS_EXTERNAL_VALIDATION` · `BLOCKED_BY_GATE` ·
`DEFERRED`.

**3.2 Evidence labels (pinned):** `CONFIRMED` · `INFERRED` · `STALE` · `CONTRADICTED` · `UNVERIFIED`.
For Arm B additionally tag the *method*: `source-read` vs `test-confirmed`.

**3.3 Claim-anchor scheme:** every contradiction/discrepancy-ledger row is keyed on the exact canonical artifact + location: `path/to/artifact.md:Lnn` (or `:§x.y`).

**3.4 CodeGraph / import-graph caveats:** `dead-unresolved` is ~100% false-positive here; `@bot.event` / `@commands.command` / `@app_commands` handlers and Cog listeners always look dead; name-collisions merge caller graphs; `callees` lists are often empty; EventBus `emit`→`bus.on` and registry-callback / prefix-dispatch edges are invisible to BOTH CodeGraph and Grimp. Never assert dead / zero-caller / no-wiring from a graph tool — grep the event-name string and the registry, run `scripts/wiring_map.py`, and read the source. `python3.10 scripts/context_map.py <file>` is the tool-agnostic import-graph substitute where available.

**3.5 CI-parity & runtime-evidence caveats:** any checker must go through `python3.10`; bare `black`/`mypy`/`pytest` give silent false results. Parity and most service/integration tests need local Postgres + Python 3.10 and may be unavailable; prefer collect-only and source/golden reads when unavailable. If a suite cannot run, mark evidence `source-read`.

**3.6 Degrade-gracefully priority ladder:** if complete depth is impossible, produce PRIMARY-owned deliverables + contradiction ledger at full depth first, and mark the rest `PARTIAL` rather than thinning the core.

**3.7 Read-only (Arms A/B/C):** no edits/commits/branches/PRs, no GitHub mutation, no plan/current-state edits, no Phase-3 approval, no new-repo code. Writing this single output report is the only permitted write.

**3.8 Exact canonical paths:** `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md` and `docs/analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md`; per-sector ledgers are `docs/current-state/S1-bot.md`, `S2-btd6.md`, `S3-ai-memory.md`, `S4-docs.md`, `S5-ops.md`.

**3.9 Shared startup route:** `.claude/CLAUDE.md` → `docs/collaboration-model.md` → `docs/current-state.md` → per-sector ledgers → `docs/AGENT_ORIENTATION.md` → `docs/owner/agent-workflow-spec.md` → `docs/owner/ai-project-workflow.md`; then rebuild planning docs, architecture contracts, and verification infra. Do not trust dated snapshots without live verification.

Subagent fallback: no subagents were used; this report is a scoped sequential investigation.

## 1. Preflight and live checkout

- Local HEAD: `cf5a234 Merge pull request #1749 from menno420/bot/dashboard-refresh`.
- Last ten local commits include #1749 dashboard refresh, #1748 `check_deferred_recovery`, #1747 `check_audit_seam`, #1746 dashboard refresh, #1745 PR-1743 verify, and ruff migration work.
- The launch-pad file was not present on local branch `work`; I read it from the requested fallback branch via GitHub raw URL and executed only C4.
- Open-PR/live-GitHub CI reconciliation was not performed beyond fetching the requested raw planning file; C4's lane is source/test truth for ownership/mutation/event paths, not Arm C's GitHub reconciliation.

## 2. Commands/searches performed

- `git log --oneline -10`
- `find .. -name AGENTS.md -print`
- `rg --files -g 'rebuild-gate-v-verification-fleet-2026-07-06.md' -g 'AGENTS.md'`
- `python - <<'PY' ... urllib.request.urlopen(raw GitHub fallback planning file) ... PY`
- `rg -n "Gate|GATE|gate|Last reconciliation|Q-0|Stage-2|mutation|EventBus|audit|sole|owner|write" ...`
- `rg -n "class EventBus|EventBus|\.emit\(|bus\.on|@.*listener|@bot\.event|@commands\.command|@app_commands|execute\(|audit|BEGIN|transaction|commit\(|rollback\(|INSERT|UPDATE|DELETE|settings|economy|inventory|xp|karma|external" ...`
- `PYENV_VERSION=3.10.20 python3.10 scripts/wiring_map.py --help`
- `PYENV_VERSION=3.10.20 python3.10 scripts/wiring_map.py disbot`
- `PYENV_VERSION=3.10.20 python3.10 scripts/wiring_map.py --check disbot`
- `PYENV_VERSION=3.10.20 python3.10 scripts/context_map.py disbot/core/events.py` — failed because `yaml` is missing.
- `PYENV_VERSION=3.10.20 python3.10 -m pytest tests/unit/invariants/test_inv_f_economy_service.py tests/unit/invariants/test_inv_g_xp_service.py tests/unit/invariants/test_no_direct_moderation_writes.py tests/unit/invariants/test_no_direct_channel_mutations.py tests/unit/invariants/test_no_direct_role_mutations.py -q` — failed at fixture import because `discord` is missing.

## 3. Confirmed facts

### EventBus semantics and truth boundaries

- **CONFIRMED/source-read:** `core.events.EventBus` is in-process, process-local, catalog-checked, and explicitly publish-accepted rather than transactional. `emit()` checks the catalogue, then invokes current handlers with per-handler timeout; handler failures increment stats/log but do not make the original mutation fail.
- **CONFIRMED/source-read:** `docs/runtime_contracts.md` and source agree that mutation result fields such as `audit_emitted`/`event_emitted` mean bus publish accepted, not subscriber success. Therefore no Gate-V plan should infer event atomicity or durable delivery from an emitted event alone.
- **CONFIRMED/source-read + wiring-map:** Event edges are string-keyed. `scripts/wiring_map.py disbot` found 30 events and passed `--check`; the pass is useful but only a lower bound because the same output flags dynamic names and parametrized emitters as requiring grep/source confirmation.

### Wiring map highlights that graph tools would miss

- **CONFIRMED/source-read + wiring-map:** `moderation.action_taken` is emitted from `services/moderation_service.py` and subscribed by two `server_logging` handlers. `audit.action_recorded` is emitted by `services/audit_events.py` and subscribed by `server_logging`.
- **CONFIRMED/source-read + wiring-map:** `ticket.open_requested` is emitted by `services/ai_tools.py` and subscribed by `cogs/ticket_cog.py`; `ticket.opened` shows as subscriber-without-static-emitter, but ticket mutation has a dynamic `_emit_bus(event, **payload)` helper, so this is not proof of dead wiring.
- **CONFIRMED/source-read + wiring-map:** governance runtime cache subscribers (`governance.visibility.changed`, `governance.cache.invalidated`, `governance.cleanup.changed`) show as no static emitters, but `governance/events.py` emits via `_emit_governance_event(event_name, payload)`. This is exactly the §3.4 trap: static blast radius would overstate deadness.
- **CONFIRMED/source-read + wiring-map:** many domain events are advisory with no subscribers today (`economy.balance_changed`, `settings.changed`, `xp.awarded`, `xp.reset`, `karma.granted`, channel/role lifecycle, etc.). That is not a contradiction if the service's DB/audit path is authoritative; it is a planning note that rebuild contracts must decide which events require durable subscribers versus remain diagnostic/advisory.

### Mutation ownership seams

- **CONFIRMED/source-read:** `docs/ownership.md` states canonical owners for economy, XP, karma, moderation, settings/governance, AI review/preset, channel lifecycle, role lifecycle, and health findings. The ownership table explicitly pairs several claims with invariant tests.
- **CONFIRMED/source-read:** Economy balance mutation is mostly service-centered. `economy_service.credit` and `debit` call `db.add_coins`, append audit, then emit `economy.balance_changed`; transaction-friendly `debit_in_txn`/`credit_in_txn` write audit inside caller-owned transactions and deliberately do not emit until the owning workflow emits after commit.
- **CONFIRMED/source-read:** XP writes route through `xp_service.award` and `xp_service.reset`; reset emits both `xp.reset` and the generic audit stream, but award emits XP events only, with no explicit audit row in the inspected snippet.
- **CONFIRMED/source-read:** Moderation's `_record_action` writes the `mod_logs` row, emits an `audit.action_recorded` companion, and emits `moderation.action_taken` with a shared `mutation_id`.
- **CONFIRMED/source-read:** `settings_mutation.SettingsMutationPipeline` invalidates the typed setting cache and emits `settings.changed` best-effort after DB commit. Source comments state that DB state is authoritative and event loss is logged/swallowed.

### Known ownership exceptions / incomplete surfaces

- **CONFIRMED/source-read:** `docs/ownership.md` explicitly says channel lifecycle does **not** yet own create/clone/overwrites/lock/arbitrary before-after reorder/category CRUD UI. The source scan confirms `proof_channel_cog` still edits permission overwrites directly, albeit with audit helper calls after the Discord edit.
- **CONFIRMED/source-read:** Channel and role lifecycle services own many Discord object mutations, but multiple service-level Discord side effects remain outside those lifecycle services by design or legacy exception (`ticket_mutation`, `setup_channel`, `counter_service`, `history_cleanup`, etc.). Treat “all channel/role mutation is owned” as CONTRADICTED; the stronger true claim is narrower: selected operator lifecycle surfaces are guarded by services and AST tests.
- **CONFIRMED/source-read:** External egress ownership is not uniformly a mutation/audit seam. `image_moderation_service` is documented as a detector routing consequential action through moderation; AI/OpenAI/provider calls were not fully audited in this C4 pass and should not be considered closed by this report.

## 4. Discrepancy ledger (§3.3 keyed)

| Plan claim key | Source evidence | Test evidence | Status | Severity | Required final-session action |
|---|---|---|---|---|---|
| `docs/ownership.md:L46` | ChannelLifecycleService owns rename/move/delete/reorder/change ops, but same row says create/clone/overwrites/lock/category CRUD are not yet owned. `proof_channel_cog` directly calls `proof_channel.edit(overwrites=...)`. | Invariant suite could not run due missing `discord`; source scan confirms exception. | CONFIRMED/source-read | Important | Do not phrase channel mutation ownership as universal; list unowned overwrite/lock paths as contract-freeze blockers or rebuild migration items. |
| `docs/runtime_contracts.md:§2` | `EventBus.emit()` returns publish-accepted and isolates handler failures; settings mutation logs/swallow event failure after commit. | `wiring_map.py --check` passed; no runtime EventBus tests run. | CONFIRMED/source-read | Blocker for event-atomicity claims | Final synthesis must forbid “event emitted means subscriber processed” as proof. Durable/event-atomic contracts need explicit transactional outbox or post-commit verifier if required. |
| `docs/ownership.md:L34` | Economy service is the documented balance owner; source shows service wrappers and transaction-friendly helpers. But non-transactional `credit`/`debit` perform balance update then audit then emit outside a single explicit transaction. | INV-F tests unavailable due missing `discord`; source-read only. | CONFIRMED/source-read with caveat | Important | Distinguish sole-writer routing from atomic audit+balance guarantee. Rebuild contract should require explicit transaction for multi-leg or money-critical flows. |
| `docs/ownership.md:L35` | XP service owns `xp.xp` mutation and emits events; award path has no inspected audit companion, reset does emit audit. | INV-G unavailable due missing `discord`. | CONFIRMED/source-read | Important | Decide whether XP award needs audit parity with economy/karma or remains event-only. Mark `NEEDS_CONTRACT_FREEZE` for audit granularity. |
| `docs/ownership.md:L37` | Moderation service writes `mod_logs`, emits audit companion and domain event with shared mutation ID. | Direct-moderation invariant unavailable due missing `discord`. | CONFIRMED/source-read | Cleanup/Important | Source supports the design; final report should still label tests source-read, not test-confirmed. |
| `docs/architecture.md:L126` | Catalogue invariant exists and `EventBus` checks known names. `wiring_map.py` sees dynamic unresolved emit/on sites that source confirms are intentional patterns in governance/ticket mutation. | `wiring_map.py --check` passed. | CONFIRMED/test-confirmed for catalogue drift lower bound | Important | Do not count subscriber-without-static-emitter as dead without string grep/source. |
| `docs/ownership.md:L52` | Governance event subscribers are registered in runtime; static wiring map shows no literal emitters because governance emits parametrized `event_name`. | `wiring_map.py --check` only advisory. | CONFIRMED/source-read | Important | Rebuild graph tooling must model registry/event-name strings or include `wiring_map.py` + grep as mandatory. |

## 5. Readiness rows for C4 systems

| System/path | Classification | Evidence | Existing oracle | Missing verification / blocker | Confidence |
|---|---|---|---|---|---|
| EventBus core (`core/events.py`) | NEEDS_CONTRACT_FREEZE | In-process publish-accepted bus; per-handler timeout/stats; source and docs align. | `wiring_map.py --check`; event catalogue tests referenced by architecture. | Decide which rebuild events require durable delivery, replay, outbox, or subscriber-success accounting. | High source confidence; medium runtime confidence. |
| Event wiring registry (`bus.emit`/`bus.on`) | READY_FOR_TEST_DESIGN | 30 events mapped; dynamic governance/ticket cases identified. | `scripts/wiring_map.py --check` passed. | Add CI/reporting that distinguishes advisory no-subscriber events from required-subscriber events. | High. |
| Economy balance mutation | NEEDS_CONTRACT_FREEZE | Sole-writer doc and service-centered source; in-transaction helpers exist. | INV-F exists but did not run here. | Define audit+balance atomicity level for all money paths; non-transaction wrappers are not enough for settle-once claims. | Medium-high. |
| XP mutation | NEEDS_OWNER_DECISION | Service owner exists; award emits events but no inspected audit row; reset audits. | INV-G exists but did not run. | Owner/architecture decision on whether XP award is auditable state or event-only progression. | Medium. |
| Karma mutation | READY_FOR_TEST_DESIGN | Ownership doc states `karma_service.give` as sole owner with audit log and `karma.granted`; current-state says reaction grants reuse it. | INV-K referenced; not run in this pass. | Run invariant suite in dependency-complete env. | Medium. |
| Moderation action mutation | READY_FOR_TEST_DESIGN | `_record_action` writes mod log + audit event + domain event; server logging subscribes. | Direct-writes test exists but not run. | Runtime/integration proof that logging routes are policy-correct and fail-safe. | Medium-high. |
| Settings scalar mutation | NEEDS_CONTRACT_FREEZE | Pipeline invalidates cache and best-effort emits after commit. | Settings tests not run. | Decide whether settings changed events are advisory or required for rebuild live-update correctness. | Medium. |
| Channel lifecycle mutation | NEEDS_SOURCE_RECONCILIATION | Service owns selected ops; explicit unowned overwrite/lock/create/category scope remains; proof channel direct overwrite edit persists. | Direct-channel test exists but did not run. | Split “owned today” vs “not yet owned” in Phase-B contracts; migrate or explicitly exempt proof-channel overwrites. | High. |
| Role lifecycle mutation | NEEDS_CONTRACT_FREEZE | Service owns create/edit/delete object lifecycle; member assignment excluded. | Direct-role test exists but did not run. | Decide if reaction-role/automation add/remove paths need unified lifecycle contract or remain separate services. | Medium. |
| Ticket/channel provisioning mutation | NEEDS_CONTRACT_FREEZE | `ticket_mutation` performs channel create/edit/delete and dynamic bus emits; likely service-owned but not under ChannelLifecycleService. | No targeted tests run. | Clarify relationship between ResourceProvisioningPipeline, TicketMutation, and ChannelLifecycleService in rebuild. | Medium. |
| External egress/moderation AI | NEEDS_EXTERNAL_VALIDATION | Ownership doc says image moderation external call is isolated and consequential action routes through moderation. | No network/provider tests run. | Arm C/D should validate provider constraints and live/fake-provider determinism; C4 only source-read. | Low-medium. |

## 6. Scoped conclusions

1. **Sole-writer and event-atomicity are different facts.** The repo has many strong service ownership seams, but event emission is intentionally publish-accepted and often post-commit/best-effort. Treat service routing as source-confirmed; treat subscriber success, replay, and atomic event delivery as unproven unless a specific path adds a transaction/outbox/oracle.
2. **The C4 load-bearing §3.4 warning is validated.** `wiring_map.py` plus grep/source reading found dynamic emitters and no-subscriber advisory events that would be misclassified by pure graph tooling. Governance and ticket events are concrete examples.
3. **Mutation ownership is uneven but explicit.** Economy, XP, karma, moderation, settings/governance, health findings, role lifecycle, and channel lifecycle have documented owners. The plan must preserve the exceptions: channel overwrites/locks, some provisioning/ticket/setup paths, role member assignment, and external egress do not collapse into one universal lifecycle owner today.
4. **Current tests could not be claimed as passing.** The invariant tests were attempted through `python3.10` as required, but the sandbox lacks `discord`; therefore all invariant-test evidence here is `source-read` or “test exists,” except `wiring_map.py --check`, which did run and passed.

## 7. Inputs required by C6/final synthesis

- Require C1/C3 to confirm invariant-test status in a dependency-complete environment, especially INV-F, INV-G, direct moderation, direct channel, and direct role mutation checks.
- Require Arm A to decide whether rebuild architecture needs durable EventBus/outbox semantics or preserves publish-accepted advisory events.
- Require owner/architecture decision on XP audit granularity and settings-event criticality.
- Require Phase-B planning delta that enumerates unowned Discord object mutations and either migrates them to lifecycle/resource services or marks them intentional exceptions with tests.
