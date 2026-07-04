# Seam-Consistency Matrix — the 14 design specs against the 7 shared-vocabulary contracts

> **Status:** `reference` — foundational design artifact (2026-07-04). **NOT SOURCE OF TRUTH** — a design contract; shipped source + the frozen upstream contracts win (Q-0120).

> **NOT SOURCE OF TRUTH for runtime — a design contract (Phase-B synthesis, method step 5:
> "decide the recurring method once — prove the ten+ specs agree").** Precedence: shipped source &
> merged PRs win (Q-0120); the owning spec wins for a shape it owns; the frozen
> **`shared-vocabulary.md`** wins where it reconciled a two-spec disagreement (those rows are the
> `RC-*` ledger). This file adds **no** new decision — it only verifies that every one of the 14
> specs writes to the **same** shape for each recurring seam, and lists every cell that is not yet
> `AGREE`.
>
> **Method.** One row per shared-vocabulary contract; one column-group per spec that **OWNS** or
> **CONSUMES** it. Each cell states the **exact shape** that spec uses + a verdict:
> - **AGREE** — the spec writes to the canonical shape verbatim.
> - **RECONCILED (RC-n · which spec changed)** — two specs disagreed; the vocab froze one winner; the
>   loser spec is named and must absorb it. Cited from `shared-vocabulary.md §⑨`.
> - **OPEN-FORK** — two specs still assume **different** shapes for the same seam, or a shape the frozen
>   vocab does not yet carry. Every OPEN-FORK is expanded in §"Disagreements + open forks" with what
>   must change to close it.
>
> **Scope.** The 7 recurring contracts named in the method: ① error-envelope / `Result` grammar ·
> ② `authority_ref → lane` · ③ audit-row semantics + `mutation_id` · ④ the idempotency-key contract ·
> ⑤ the restart-safety pattern · ⑥ `EventSpec.delivery` · ⑦ config/secret + the data-plane rail.
> Specs: `01`…`05` (strand-1 kernel spine), `06`…`09` (strand-2 runtime durability), `10`…`14`
> (strand-3 cross-cutting).
>
> **Fork-numbering note (2026-07-04).** The fork identifiers below are aligned to the **canonical
> PIN / owner-register numbering** used across the rebuild (F-1 poll · F-2 K7-draft-entry · F-3 intent
> posture · F-4 `actor_type` · F-5 background `Surface`). An earlier draft of this matrix used a local,
> divergent order; it was renumbered to the canonical order in this pass so no consumer cross-references
> two numberings. See the **Resolution log** (§8).
>
> **Headline result (updated 2026-07-04).** Of the touched cells, **56 AGREE** and the **four
> reconciliations applied this pass (F-1 / F-2 / F-4 / F-5)** now hold as **RECONCILED** across every
> cell they touched — the specs have absorbed them in source (verified). All prior reconciliations
> (RC-1…RC-15) still hold. **One OPEN-FORK remains: F-3 (intent posture, `14`↔`05`)** — owner-gated,
> **carried to owner register PG-2**, not resolved by edit. None of the applied four ever blocked a
> build; they are now closed and the specs are buildable-consistent.

---

## 0. The five forks at a glance (read this first) — 4 RESOLVED · 1 CARRIED

| # | Seam | Specs | The disagreement | Status (2026-07-04) |
|---|---|---|---|---|
| **F-1** | ⑤ restart-safety / ⑥ delivery — **poll topology** | `08` ↔ `09` | `08` registered the relay as a **`PollLane` on `09`'s `PollSupervisor`** (5 s); `09` (as drafted) said the relay was **its own supervised `RELAY_TASK(Interval 1s)`, "NOT my lane."** Built as drafted the outbox was **unhosted**. | **✅ RESOLVED — applied.** PIN-1: **`09` fixed** — it now HOSTS `OutboxRelayLane` + `OutboxReaperLane` as `PollLane`s on its one `PollSupervisor` at 5 s; the standalone-`RELAY_TASK`/1 s language is withdrawn. `08` already cited `09` as host (unchanged). → RC-20. |
| **F-2** | ③/④ — **K7 engine entry the draft consumes** | `06` ↔ `07` | `07` named `apply(op)` "the draft's per-op apply"; `06` retired `apply(op)`, used per-op `run(spec, ctx)` (engine-owned txn + post-commit EFFECT legs), and mis-stated `run_ref` as "NOT in 07's API." | **✅ RESOLVED — applied.** PIN-2: **`06`+`07` fixed** by **caller type** — EFFECT-bearing draft ops go through `run(spec, ctx)` per-op (per-op-atomic + idempotent-resume, **not** one shared txn); `run_ref`/`apply` exist but are external-conn **pure-DB** only (scheduler / invariant / version callers), `atomic_db_only`-fenced. Fence scope no longer names any draft `op_kind` (unblocks the 10-channel canary). Resolved by **caller type** (F-2 co-decision — no single RC row; see the Resolution log). |
| **F-3** | ⑦ config/intent rail — **intent-denial posture** | `14` ↔ `05` | `05 §3.1` declares `message_content`/`members` **`required=True` ⇒ `FAILED_STARTUP`** on denial. `14 §2.B` flips them to **`required=False` + `IntentPosture.DEGRADE`** (boot slash-only). `14` routes this as a seam correction to `05`. | **⏸ CARRIED → owner register PG-2.** PIN-5: **NOT resolved by edit** — owner-gated. `05` keeps fail-closed (`FAILED_STARTUP` on unapproved privileged intent) as the safe default until the owner rules; the fork stays in the question register. No spec edit closes it. |
| **F-4** | ② authority — **`ActorRef.actor_type`** | `02` + vocab §⑩ (`09`/`11` assumed it) | `09`/`11`'s `SYSTEM_ACTOR`/`SWEEP_ACTOR` need `ActorRef.actor_type ∈ {system, backfill}` to drive K7's scripted-bypass. Frozen `ActorRef` (vocab §⑩) had no `actor_type`. | **✅ RESOLVED — applied.** PIN-3: **`02` leaf + vocab §⑩ fixed** — `ActorRef` gains `actor_type: str = "user"` (value set `{user, system, backfill, setup_delegate}`); `SYSTEM_ACTOR="system"`, `SWEEP_ACTOR="backfill"`; K7 maps `ctx.actor.actor_type → AuthorityRequest.actor_type` into `resolve_authority`'s scripted-bypass. `09`/`11` already consumed it. → RC-18. *(Distinct from RC-12 `member_tier`, still pending on `02`.)* |
| **F-5** | ① error-envelope — **background `Surface` member** | `02` (owns) + `07`/`09`/`11` (consume) | `from_exception` needs a `surface`; a scheduler fire / sweep-repair has none. `09` used `surface="scheduler"`; `11 §4 Q4` flagged `scheduler` vs `maintenance` and refused to fork it. Frozen interaction `Surface` carried neither, and `target` was non-optional. | **✅ RESOLVED — applied.** PIN-4: **`02` + `07`+`09`+`11` fixed** — `Surface` gains **ONE** background member `MAINTENANCE = "maintenance"` (covers scheduler fires AND sweep-repairs); `from_exception`'s `target` widened to `TargetRef \| None`; background fires call `from_exception(exc, surface=Surface.MAINTENANCE, target=None)`. Both `09` (§3.8) and `11` (§2.2/§4 Q4/§8.2) adopt it; `07`'s K7 leg-exception path pinned to it. → RC-19. |

---

## 1. Seam ① — THE ERROR-ENVELOPE / `Result` GRAMMAR

**Canonical (vocab §① / §⑦.1 / §0, RC-1/RC-6/RC-8/RC-19):** outcome vocab = the 5 real constants
`SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED` (`services/lifecycle/contracts.py:48-52`); dispatch
return = `WorkflowResult | None` (K7 **design** superset of `LifecycleResult`, no shipped class);
`StageResult` is the message-pipeline substrate, **never** a dispatch return; `from_exception(exc, *,
surface: Surface, target: TargetRef | None, …)` + `ErrorClass{NONE,USER_ERROR,DENIED,TRANSIENT,BUG}` +
`DenialReason` (leaf `sb/spec/outcomes.py`, RC-6); the background `Surface.MAINTENANCE` member (RC-19)
covers headless fires; `bug → BLOCKED` nuance lives in `error_class`+`reason`, never a 6th outcome.

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **02** | **OWNS** `from_exception`, `Result`, `ErrorEnvelope`, `ErrorClass`, `Surface`; leaf owns `DenialReason` | The frozen table (5 rows) → §2.7 outcomes; `Result.outcome` copies `WorkflowResult.outcome` through; `StageResult` dropped from dispatch grammar (§3.6); **`Surface` now carries the `MAINTENANCE` background member and `from_exception.target` is `TargetRef \| None`** (§3.1/§3.3, PIN-4) | **AGREE** (RC-1 framing verbatim; RC-19 owner) |
| **01** | Consumes | `audit_completeness`/`never_strand` read the `WorkflowRef` return = `WorkflowResult\|None`; `core/contracts.py` re-confirmed absent | **AGREE** (RC-1 mis-cite fixed) |
| **03** | Consumes | trigger-set rejection ⇒ `outcome=BLOCKED` on the **real** `contracts.py:50` (§3.4) | **AGREE** |
| **04** | Consumes | denial ⇒ resolver maps to `BLOCKED`/`error_class=denied`; engine returns `allowed:bool`+`DenialReason` | **AGREE** |
| **05** | Consumes | `DBUnavailable(ConnectionError)` routes through 02's **existing** `ConnectionError` transient row → transient/`DISCORD_FAILED` (RC-8, zero-edit) | **AGREE** |
| **06** | Consumes | `from_exception(exc,surface,target,section_label)`; `DenialReason` incl. `CONFIRM_DECLINED`; op failures → §2.7 outcomes (§3.6 table) | **AGREE** |
| **07** | **OWNS** `WorkflowResult` (design superset) | copies outcome through; `ConfirmRequired` is a **control signal, NOT a `from_exception` input** (§3.3 step 2); error-**return** contract (catch+roll-back+return, never raise); **K7 leg-exception path classifies via `from_exception(exc, surface=Surface.MAINTENANCE, target=None)`** (§3.3 step 4b, PIN-4) | **AGREE** (RC-19 consumer) |
| **08** | Consumes | `WorkflowResult` design type; `outcome` values in `event_outbox` are the frozen 5 | **AGREE** |
| **09** | Consumes | classifies fire/compensation exceptions via `from_exception` with **`surface=Surface.MAINTENANCE, target=None`** (§3.8) | **AGREE** (RECONCILED — F-5/RC-19, applied) |
| **11** | Consumes | sweep-repair exceptions via `from_exception` with **`surface=Surface.MAINTENANCE, target=None`** (§2.2/§4 Q4); the earlier `scheduler`/`maintenance` fork is closed | **AGREE** (RECONCILED — F-5/RC-19, applied) |
| **13** | Consumes | reads only `WorkflowResult.{outcome, mutation_id}` (design §2.7 fields) | **AGREE** |

*Cells: 11 AGREE (09/11 RECONCILED via F-5/RC-19 this pass).*

---

## 2. Seam ② — `authority_ref → LANE` (+ owner-override-once + channel-access + transparency)

**Canonical (vocab §② / §⑨ RC-2/3/4/5/12/13/14/15/18 · owner: `04`/K6):** one `authority_ref: str` on
**six** spec types; `classify_authority_ref → Lane{CAPABILITY,TIER}` (in `sb/spec/authority.py`, RC-3);
`AuthorityRequest` (discord-free, carries `member_tier` **and** `actor_type`); `AuthorityDecision`
**10-field** (04 owns; 02 imports — RC-2); `resolve_authority` owner-override-once-at-top;
`ChannelAccessDecision` **8-field** with `detail` (RC-13); `AccessMode` = shipped value strings;
`denial_message` **engine-generated** (RC-14); transparency rides **`TransparencySink` port +
`command.dispatched` `override_applied` flag** (RC-15); `owner_override_holds(user_id,is_member)` the
single predicate; `ActorRef.actor_type` additive field (RC-18) feeds the scripted-bypass.

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **04** | **OWNS** all of the above | 10-field `AuthorityDecision`; `Lane{CAPABILITY,TIER}`; 8-field `ChannelAccessDecision(+detail)`; `AccessMode` shipped strings; `TransparencySink`; discord-free `AuthorityRequest.member_tier`+`actor_type` | **AGREE** (owner) |
| **01** | Consumes | P4 calls `validate_authority_ref(ref)` on **six** spec types; `""`⇒ADMIN-floor always-valid; P3/P4 split | **AGREE** (RC-7 done) |
| **02** | Consumes (WRITTEN pre-hardening) | **`ActorRef` now carries `actor_type` (RC-18 applied, §3.1)**; still carries `AuthorityLane{CONFIG_GOVERNANCE,DOMAIN}`, **5-field** `AuthorityDecision`, `ActorRef` **without `member_tier`**, channel-access **not** threaded `owner_override`, transparency sink **unnamed** | **RECONCILED — 02 still the loser (RC-2/3/4/5/12/13/14/15); must absorb 04's shapes.** *(F-4/RC-18 `actor_type` now landed; RC-12 `member_tier` still pending.)* |
| **03** | Consumes | P3 owns capability **format + reserved-prefix owner** (`{sub}.{res}.{action}`); P4 owns lane resolution — no overlap | **AGREE** |
| **06** | Consumes | `resolve_authority`, `AuthorityRequest`, 10-field `AuthorityDecision`, `owner_override_holds`; `resolve_draft_accept` = **AND over every distinct op `authority_ref`** | **AGREE** |
| **07** | Consumes | leg-0 `resolve_authority(AuthorityRequest(spec.authority_ref, actor…))`; reads `AuthorityDecision.{allowed,denial_message}`; passes `ctx.actor.member_tier` | **AGREE** |
| **09** | Consumes | scripted-bypass on `actor_type ∈ {system,backfill}`; `SYSTEM_ACTOR.actor_type="system"` on the applied **`ActorRef.actor_type`** field (§3.7) | **AGREE** (RECONCILED — F-4/RC-18, applied) |
| **11** | Consumes | `SWEEP_ACTOR.actor_type="backfill"` on the applied `ActorRef.actor_type` field (§2.2); **consumes** it, no longer a flagged correction | **AGREE** (RECONCILED — F-4/RC-18, applied) |
| **14** | Consumes | invoker `member_tier` computed from the `INTERACTION_CREATE` payload (needs no privileged intent); shape ②/RC-12 | **AGREE** |
| **10** | Consumes (asserts) | class-13 owner axis **asserts** the single `is_platform_owner` AST fence + `TransparencySink` (RC-15) exist | **AGREE** |

*Cells: 9 AGREE (09/11 RECONCILED via F-4/RC-18 this pass) · 1 RECONCILED-pending (02, authority batch).*

---

## 3. Seam ③ — AUDIT-ROW SEMANTICS + `mutation_id`

**Canonical (vocab §③ · owners: shipped `emit_audit_action` 11-field → K7; dispatch-trace `02`;
`audit_log` central row `07`; durable twin `enqueue_audit_action` `08`):** **one dispatch-trace +
zero-or-more mutation-audit rows per command**; mutation audit = the frozen **11 keyword-only fields**
keyed by `mutation_id` (pipeline UUID, the link between `audit.action_recorded` and the DB row);
single-op ⇒ 1 row, batched lifecycle op ⇒ **1** row, compound draft ⇒ N rows correlated by a shared
id. Transparency notice is **neither** seam (RC-15). Correlation is a **`audit_log.correlation_id`
column**, never a 12th bus field (07 §5 / 08 §5.1 / 06 §12 — **RECONCILED, RC-16**).

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **07** | **OWNS** `audit_log` central row + `correlation_id` column + `emit_central_audit` over the durable twin | one `audit_log` row per invocation, `mutation_id` PK, legs as `detail` JSONB, `correlation_id=ctx.correlation_id`; never N rows | **AGREE** (owner) |
| **02** | **OWNS** the dispatch-trace | `command.dispatched` `EventSpec(observability_only=True, owner_subsystem="kernel")`; `override_applied`/`base_allowed` **derived** from `AuthorityDecision`; never bypasses `emit_audit_action` | **AGREE** (derived-flag shapes per RC-2/5/15) |
| **01** | Consumes | P6 `audit_completeness`: `effect="mutating"` ⇒ MUST carry a `WorkflowRef` (compile proxy for "routes through `emit_audit_action`") | **AGREE** |
| **04** | Consumes | `TransparencyAudit` does **NOT** fill the 11-field seam; rides `TransparencySink` + the trace flag (RC-15) | **AGREE** |
| **05** | Consumes | `idempotency_keys.result_ref` points to the audit/mutation id | **AGREE** |
| **06** | Consumes | `ctx.correlation_id = draft_id` written to each op's `audit_log.correlation_id`; **one** central row per op; the 11-field bus payload unchanged | **AGREE** (RC-16 correlation-by-column) |
| **08** | **OWNS** `enqueue_audit_action(conn, **11 fields)` durable twin | delivers the byte-identical `audit.action_recorded`; adds the `correlation_id` column | **AGREE** |
| **09** | Consumes | fire's mutation audits **inside** `run_ref`'s central row on my conn; due-queue arm/claim/fire bookkeeping is **not** an auditable mutation | **AGREE** |
| **10** | Consumes | `erasure_ref` = `WorkflowRef` ⇒ one `emit_audit_action` per store; bare `HandlerRef` erasure = `SEMANTIC_VIOLATION` (reuses §③.4) | **AGREE** |
| **11** | Consumes | repair = `WorkflowRef` central row `mutation_type="invariant_repair:<id>"`; `sb_invariant_sweep_log` is kernel-internal, **not** audited | **AGREE** |
| **13** | Consumes | reverse-import LEDGER tier re-inserts by `mutation_id` `ON CONFLICT DO NOTHING`; notes `audit_log` is the **forensic** substrate, not a complete money log (legacy hole closed for new-bot by §③.4) | **AGREE** |

*Cells: 11 AGREE. No divergence — the correlation-id-by-column reconciliation (RC-16) holds across 06/07/08.*

---

## 4. Seam ④ — THE IDEMPOTENCY-KEY CONTRACT

**Canonical (vocab §④ · owner `05`/K3):** `IdempotencyKey{namespace, guild_id, dedup_token}`,
`render()=f"{ns}:{gid}:{tok}"`; `once`/`record_outcome`/`read_outcome` on a **txn-bound `conn` from
`db.transaction()`**; `PriorOutcome{outcome, result_ref, first_seen_at}`; `idempotency_keys` table.
The "three sites" table (dispatch dedup · confirm re-entry `request_id` · leg/relay) is **non-exhaustive
by design** — siblings add more sites, constructed identically.

| Spec | Owns/Consumes | Exact `dedup_token` / usage | Verdict |
|---|---|---|---|
| **05** | **OWNS** the shape + table + `db.transaction()` | `render()`, `once()` INSERT…ON CONFLICT DO NOTHING RETURNING; atomic guard+effect+outcome pattern | **AGREE** (owner) |
| **02** | Consumes | dispatch dedup checked at **step 5** (durable `IdempotencyKey`); confirm re-entry uses in-memory **`request_id`** (a uuid, **not** an `IdempotencyKey`) | **AGREE** |
| **06** | Consumes (via K7) | `dedup_token = f"{draft_id}:{op_seq}"` supplied to K7's per-op `once()` (completes §④.2); draft ops ride K7 `run(spec,ctx)` per-op (F-2 resolved) | **AGREE** |
| **07** | Consumes | `DedupKeySpec`; `DURABLE_ONCE ⇒ once()+record_outcome` namespace=`op_key`; farm-collect `dedup_key=(user_id,interaction_id)` (cross-user-safety) | **AGREE** |
| **08** | Consumes | outbox `dedup_key` **IS** `IdempotencyKey.render()`; `UNIQUE(dedup_key)` = the exactly-once capture; per-producer disambiguator `…:{event_name}`/`…:{emit_index}` | **AGREE** |
| **09** | Consumes (+adds 4th site) | fire `dedup_token=f"{task_id}:{fire_epoch}"` **deterministic** (fixes the shipped uuid4); version-reject `{table}.version_reject:{…}`; GLOBAL slot key normalized via `COALESCE(guild_id,0)` (sweep fix, §5) | **AGREE** (additive; GLOBAL double-arm closed) |
| **11** | Consumes (+adds 5th/6th) | cadence `{invariant_id}.sweep:{epoch}` + repair `{invariant_id}.repair:{row_id}:{fingerprint}`; §8.1 flags §④.2 non-exhaustive | **AGREE** (additive) |
| **12** | Consumes | rotation `once(IdempotencyKey("credential.rotation", 0, f"{name}:{horizon_epoch}"))` — horizon-stable, armed as a durable OneShot on 09's due-queue (§2.B) | **AGREE** (additive site) |
| **13** | Consumes | reverse-import ledger by `mutation_id` PK; `once()`-tied | **AGREE** |
| **14** | Consumes | `platform.guildcap` latch (or a settings row) for the ~75/90 fire-once | **AGREE** |

*Cells: 10 AGREE. The additive-sites note is a completeness annotation, not a shape divergence.*

---

## 5. Seam ⑤ — THE RESTART-SAFETY PATTERN

**Canonical (vocab §⑤ · owners `05` durable store + drain gate, `09` scheduler completer):** durable
state in DB tables (not memory); **drain gate** at resolver step 0 (`can_accept_commands()`; RC-9);
**boot-reconcile fires overdue exactly once, after `/ready` 200 = RUNNING** (RUNNING-only, STARTING⇒503,
05 §3.8); **fast-release handoff** covered by `once()`+`db.transaction()` uniformly. The shared poll host
is `09`'s `PollSupervisor` + `PollLane` port, and **`09` hosts the outbox relay/reaper lanes** (RC-20).

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **05** | **OWNS** the store + drain gate + `/ready` | `/ready` RUNNING-only 200; fast-release releases the lock immediately; `once()` covers the overlap | **AGREE** (owner) |
| **09** | **OWNS** scheduler completion + hosts the poll lanes | durable `sb_due_queue`; boot-reconcile after RUNNING (bounded `claim_due` SKIP-LOCKED loop); **one `PollSupervisor` hosting `DueQueueLane` + `ExpiryJanitorLane` + `OutboxRelayLane` + `OutboxReaperLane`** (non-exhaustive roster) at 5 s; `SYSTEM_ACTOR` | **AGREE** (RECONCILED — F-1/RC-20, applied; 09 now hosts the outbox lanes) |
| **02** | Consumes | step-0 drain gate `can_accept_commands()` on **every** surface (RC-9); confirmations survive nothing | **AGREE** |
| **06** | Consumes | drafts durable; **no** auto-apply on boot; `ExpiryJanitorLane` + stuck-`APPLYING` reaper (`reap_stuck_applying` CAS, `DRAFT_APPLY_STUCK_TTL_S=900s`) on **09's** `PollSupervisor` | **AGREE** (stuck-APPLYING TTL pinned, §6) |
| **07** | Consumes | stateless; arms no timers; **no** boot-reconcile (supplies the `run_ref` substrate the scheduler fires through) | **AGREE** |
| **08** | Consumes | relay `reconcile_on_boot` = **no-op** (first post-RUNNING tick IS the reconcile); supervisor gates on RUNNING first; cites **09 as the host** of `OutboxRelayLane`+`OutboxReaperLane` | **AGREE** (RECONCILED — F-1/RC-20, applied) |
| **11** | Consumes | `InvariantSweepLane` a `PollLane` on **09's** supervisor; cadence via `{invariant_id}.sweep:{epoch}` `once()`; `reconcile_on_boot` re-runs incomplete epochs | **AGREE** (consistent with 08/09's registered-lane model) |
| **12** | Consumes | rotation read-back waits for `/ready` 200 (post-boot instance); armed as a durable OneShot on 09's due-queue so `reconcile_on_boot` re-arms it; `once()`+phase ledger guard double-issue | **AGREE** (durable-timer home, §2.B) |
| **13** | Consumes | `SB_VERIFY_BOOT` **suppresses** boot-reconcile + relay (T-7); requires `SB_DATA_PLANE=test` | **AGREE** (contained) |
| **14** | Consumes | `platform.guildcap.<t>` durable fire-once latch, restart-safe | **AGREE** |

*Cells: 10 AGREE (08/09 RECONCILED via F-1/RC-20 this pass).*

---

## 6. Seam ⑥ — `EventSpec.delivery` (durable delivery)

**Canonical (vocab §④/§⑤ skeleton · owner `08`):** `DeliveryClass{AT_LEAST_ONCE, BEST_EFFORT}` **home =
`sb/spec/events.py`** (07 imports it, no local copy — RC-17 per 08 §12.1 / 07 §8 fork F);
`EventSpec.delivery` [S] default `BEST_EFFORT`; `AT_LEAST_ONCE` ⇒ in-txn `event_outbox` row +
post-commit relay; the outbox `dedup_key` is an `IdempotencyKey.render()`; `enqueue_all(emits, ctx,
result, *, conn) -> BestEffortBatch`. The relay/reaper run as `PollLane`s on **09's** `PollSupervisor`
(RC-20).

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **08** | **OWNS** `DeliveryClass` + `EventSpec.delivery` + `event_outbox` + relay | canonical enum home (`sb/spec/events.py`); `enqueue`/`enqueue_all`/`enqueue_audit_action`; exactly-once-capture / at-least-once-relay / handler-dedup contract; `OutboxRelayLane`+`OutboxReaperLane` registered on **09's** supervisor | **AGREE** (RECONCILED — F-1/RC-20 on the host) |
| **07** | Consumes | **imports** `DeliveryClass` from `sb/spec/events.py`; `EventEmitSpec.delivery`; `enqueue_all` in-txn at step 4e + `emit_after_commit()` at step 6 (the two-call protocol — confirmed consistent, 08 §12.5) | **AGREE** (RC-17 — one enum, no drift) |
| **05** | Consumes | `observability_only=True ⇒ delivery==BEST_EFFORT` (the compile fence) | **AGREE** |
| **06** | Consumes | `AT_LEAST_ONCE` emits via K7's `enqueue_all` on the op txn | **AGREE** |
| **09** | Consumes/hosts | the outbox relay/reaper are `PollLane`s **09 HOSTS** on its one `PollSupervisor` at 5 s; the standalone `Interval(1s)` `RELAY_TASK` model is withdrawn | **AGREE** (RECONCILED — F-1/RC-20, applied) |
| **11** | Consumes | Discord output from a sweep-repair = an `AT_LEAST_ONCE` outbox emit on the sweep conn (never a post-commit EFFECT leg) | **AGREE** |
| **13** | Consumes | scheduled Discord output rides an `AT_LEAST_ONCE` outbox emit | **AGREE** |

*Cells: 7 AGREE (09 RECONCILED via F-1/RC-20 this pass; cross-listed with ⑤).*

---

## 7. Seam ⑦ — CONFIG / SECRET GRAMMAR + THE DATA-PLANE RAIL

**Canonical (vocab §⑥ · owner `05`):** `ConfigSpec`/`SecretSpec`/`ConfigPosture`/`ConfigType`(+CSV)/
`IntentSpec`; one typed frozen `Config` attribute per field (verbatim env name, RC-10); `parse_bool` the
one grammar; `preflight()` first in the composition root; `assert_data_plane` the 4th rail (non-`test`
DSN ⇒ `RefuseBoot`); `CONFIG_FIELDS = 47`; `INTENT_CONTRACT` (`message_content`/`members`, both
privileged, **`required=True`** — until PG-2 rules on F-3).

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **05** | **OWNS** the grammar + rail + `INTENT_CONTRACT` | `CONFIG_FIELDS` (47); `assert_data_plane`; `SB_PROD_ATTEST` presence-gated `SecretSpec`; `message_content`/`members` `required=True` fail-closed | **AGREE** (owner) |
| **12** | Consumes | **`CredentialSpec` a SIBLING leaf** (`sb/spec/credentials.py`) — does **not** mutate `SecretSpec`/§6.1; `config_ref` names the `SecretSpec.env_var`; consumes the data-plane rail | **AGREE** (sibling-leaf discipline, no §6.1 amendment) |
| **13** | Consumes (+adds) | `SB_VERIFY_BOOT: BOOL` = an **additive 48th** operational `ConfigSpec` (§8.5 flags "47 total" not closed); `SB_DATA_PLANE=test` forced for verify | **AGREE** (additive; vocab count 47→48 to absorb) |
| **14** | Consumes (+corrects) | extends `IntentSpec` with `IntentPosture`+`degrades`; **flips `message_content`/`members` `required=True → False` + `posture=DEGRADE`** (seam correction to `05`) | **OPEN-FORK F-3** (owner-gated → PG-2) |
| **10** | Consumes (asserts) | class-13 asserts no un-redacted `SecretSpec` on any log/`/metrics`/diag path (`SecretSpec.redact`, 05 §3.2/3.8) | **AGREE** |
| **11** | Consumes | `INVARIANT_ENFORCE(id)` `settings_keys` constant via the config/settings rail (never `os.getenv`) | **AGREE** |

*Cells: 5 AGREE · 1 OPEN-FORK (F-3, owner-gated → PG-2). Plus two additive-not-fork notes: `SB_VERIFY_BOOT`
(47→48) and the existing owner-gated **SF-d** `SB_PROD_ATTEST` custody source (12 CL-5b) — both already
tracked, neither new.*

---

## 8. Disagreements + open forks (every non-AGREE cell, with what changed / what must change)

### F-1 — Poll topology: where does the outbox relay run? (`08` ↔ `09`) — **✅ RESOLVED (applied 2026-07-04, PIN-1)**
- **The disagreement:** `08` registered the relay as an `OutboxRelayLane` on `09`'s shared
  `PollSupervisor` (5 s, `reconcile_on_boot` a no-op); `09` (as drafted) said the relay was **its own**
  supervised `ManagedTaskSpec(Interval 1s)` "I do NOT host or boot-reconcile it." Each cited the other
  as having decided the opposite way; built as drafted the relay was **unhosted** and the cadence
  ambiguous (5 s vs 1 s).
- **Resolution (PIN-1 — `09` fixed):** `09` now **HOSTS** `OutboxRelayLane` + `OutboxReaperLane` as
  `PollLane`s on its ONE `PollSupervisor` at the shared **5 s** cadence; the standalone-`RELAY_TASK` /
  `Interval(1s)` / "not-my-lane" / self-reconciling language is **withdrawn everywhere in `09`** (header,
  §1, §2 `poll.py` row, §3.6, §4, §6, §8, §11, §12 #4). `09`'s lane roster is now explicitly
  **non-exhaustive**: due-queue + draft janitor + outbox relay/reaper today, with the invariant sweep
  (11) + credential-rotation lanes as declared future riders. `08` already cited `09` as host and is
  unchanged. Correctness rationale (in `09` §1/§12): under `AT_LEAST_ONCE` audit delivery, an unhosted
  relay = silent total loss of the operator audit trail on every restart. **Registered as RC-20.**

### F-2 — K7 engine entry the draft pipeline consumes (`06` ↔ `07`) — **✅ RESOLVED (applied 2026-07-04, PIN-2)**
- **The disagreement:** `07` named `apply(op, conn)` "the draft-pipeline per-op apply" (external-conn,
  **no** EFFECT legs) and claimed the draft runs N legs in one shared txn; `06` had retired `apply(op)`,
  used per-op `run(spec, ctx)` (engine-owned txn; **resource-create channel ops run as post-commit
  EFFECT legs**), and mis-mapped `07`'s API as lacking `run_ref`.
- **Resolution (PIN-2 — `06`+`07` fixed by caller type):** EFFECT-bearing draft ops go through
  **`run(spec, ctx)` per-op** — own txn + post-commit EFFECT legs; **per-op-atomic + idempotent-resume**,
  **NOT** one shared txn. `run_ref`/`apply` **do** exist in `07`'s API but are for **external-conn
  PURE-DB callers only** (scheduler `ManagedTaskSpec` handlers; invariant `repair_ref`s; version
  `compensation_ref`s), and `07`'s `atomic_db_only` fence scopes to **those callers only** — the
  "…or a draft `op_kind` mapping" clause is **removed** from the fence, so the flagship 10-channel
  resource-create draft (whose ops each bear a Discord `create_channel` EFFECT leg) is no longer
  CI-red. `06` reframed the cross-op shared-txn as **structurally unavailable** to this pipeline (its
  EFFECT legs are ineligible for the pure-DB fence), not a pending upgrade; `07` dropped the fork-A
  shared-txn claim and re-anchored stale line cites. **F-2 resolved in both specs (06 §3.5/§4/§8/§9/§10/§12;
  07 §1/§3.2/§3.3/§3.6/§4/§8/§10/§11).**

### F-3 — Intent-denial posture: `required=True` fail-closed vs `DEGRADE` (`14` ↔ `05`) — **⏸ CARRIED → owner register PG-2 (PIN-5)**
- **`05 §3.1`** declares `message_content`/`members` **`required=True`**; `assert_intents` accrues a
  `ConfigError → StartupError → FAILED_STARTUP` when an unapproved privileged intent is missing in a
  non-`test` plane — the bot refuses to boot.
- **`14 §2.B`** flips both to **`required=False` + `IntentPosture.DEGRADE`** (+ `degrades` set), so
  denial **boots slash-only** with an explicit `DegradedCapability` notice; adds the enforced invariant
  `required == (posture is REQUIRED)`. `14` routes this as a **seam correction to `05`**.
- **Status (PIN-5):** **owner-gated — NOT resolved by edit.** `05` keeps fail-closed as the safe default
  until the owner rules; the fork stays in the question register as **PG-2**. Recommendation (14's):
  adopt `DEGRADE` — fail-closed darks the whole bot when it could serve every slash command, and
  slash-first survivability is the growth posture. `05 §3.1` gains `IntentPosture`/`degrades` and the
  mirror-invariant **only once PG-2 is approved.** No spec edit closes this in this pass.

### F-4 — `ActorRef.actor_type` additive field (`02` + vocab §⑩; `09`/`11` assumed it) — **✅ RESOLVED (applied 2026-07-04, PIN-3)**
- **The gap:** the frozen `ActorRef` (vocab §⑩) = `{user_id, is_guild_operator, is_bot_owner, is_dm,
  member_tier}` — **no `actor_type`**. `09`'s `SYSTEM_ACTOR` (`actor_type="system"`) and `11`'s
  `SWEEP_ACTOR` (`actor_type="backfill"`) need it so K7 maps `AuthorityRequest.actor_type =
  ctx.actor.actor_type` and hits `resolve_authority`'s scripted-bypass (§②.3).
- **Resolution (PIN-3 — `02` leaf + vocab §⑩ fixed):** `ActorRef` gains **`actor_type: str = "user"`**
  (value set `{user, system, backfill, setup_delegate}` per vocab §2.3 `AuthorityRequest`), added as the
  last field to preserve dataclass ordering; `02 §3.1/§3.2` document that the resolver builds the
  `AuthorityRequest` carrying `req.actor.actor_type` — always `"user"` on an interaction surface, with
  the `"system"`/`"backfill"` bypass values reaching `resolve_authority` only via the headless K7/09/11
  path. `09`/`11` already consumed the field and no longer carry it as a flagged correction. **Registered
  as RC-18.** *(Distinct from **RC-12** `member_tier`, a DIFFERENT additive field still pending on `02`'s
  ActorRef — see §9.)*

### F-5 — Background `Surface` member for headless fires (`02` owns; `07`/`09`/`11` consume) — **✅ RESOLVED (applied 2026-07-04, PIN-4)**
- **The gap:** `from_exception(exc, *, surface, target)` required both, but a scheduler fire / invariant
  sweep-repair has no interaction origin. The frozen interaction `Surface` (RC-11) had no background
  member; `09` used `surface="scheduler"`, `11 §4 Q4` refused to fork `scheduler` vs `maintenance`.
- **Resolution (PIN-4 — `02` + `07`/`09`/`11` fixed):** `02`'s `Surface` enum gains **ONE** background
  member **`MAINTENANCE = "maintenance"`** (covers scheduler fires AND invariant sweep-repairs — NOT a
  per-sibling split); `from_exception`'s `target` widens to **`TargetRef | None`**; background fires call
  `from_exception(exc, surface=Surface.MAINTENANCE, target=None)`, where `surface`/`target` only enrich
  `user_message` (a headless fire discards the copy — the classifier core `exc → error_class → reason →
  outcome → retryable` is surface/target-independent). Adopted by `09` (§3.8) and `11` (§2.2/§4 Q4/§8.2),
  and pinned into `07`'s K7 leg-exception path (§3.3 step 4b + §4 Consumes). `11`'s Q4 flips to
  **RESOLVED / vocab freeze — CLOSED**; the earlier `scheduler`/`maintenance` fork is superseded, no
  second token. **Registered as RC-19.**

### Resolution log (applied 2026-07-04)

This pass records the **four mechanically-reconciled forks now applied to the specs** and the **one
carried to the owner**. Fork identifiers are the canonical PIN / owner-register numbering (see the
fork-numbering note in the header; an earlier draft's local order was renumbered here so no consumer
cross-references two numberings).

| Fork | Resolution | Specs changed | RC |
|---|---|---|---|
| **F-1** poll topology (`08`↔`09`) | **RESOLVED — applied.** `09` HOSTS `OutboxRelayLane`+`OutboxReaperLane` on its one `PollSupervisor` at 5 s; standalone-1 s-loop model withdrawn; roster non-exhaustive. `08` unchanged (already host-citing). | **09** | RC-20 |
| **F-2** K7 draft entry (`06`↔`07`) | **RESOLVED — applied.** By caller type: draft EFFECT ops → `run(spec,ctx)` per-op (per-op-atomic + idempotent-resume); `run_ref`/`apply` = external-conn pure-DB only, `atomic_db_only`-fenced with no draft `op_kind` in scope (10-channel canary un-blocked). | **06, 07** | — (F-2 co-decision) |
| **F-3** intent posture (`14`↔`05`) | **CARRIED — not resolved by edit.** Owner-gated → **register PG-2**. `05` keeps `required=True` fail-closed floor; `14`'s DEGRADE flip stays a proposed correction until the owner rules. | *(none — carried)* | — |
| **F-4** `ActorRef.actor_type` (`02`+vocab) | **RESOLVED — applied.** `ActorRef` gains `actor_type: str = "user"` (`{user,system,backfill,setup_delegate}`); K7 maps it into `AuthorityRequest.actor_type`; `09`/`11` consume. | **02** (+ vocab §⑩) | RC-18 |
| **F-5** background `Surface.MAINTENANCE` (`02`+`07`/`09`/`11`) | **RESOLVED — applied.** `Surface` gains one `MAINTENANCE` member; `from_exception.target → TargetRef\|None`; `09`/`11` classify under `MAINTENANCE`, `07`'s leg-exception path pinned to it. | **02, 07, 09, 11** | RC-19 |

**Also registered in the reconciliation layer this pass (was omitted before):** the **`ChannelEmitter`
send-egress port** (`10` class-13 / Q-D26) — a new `kernel/interaction` egress port + AST fence — is now
carried as a **pending 02/K8 seam correction, RC-21**, parallel to RC-12/F-4 (the additive-field
class). It is homed as **Q-D26** in the question register and referenced by `10 §2.A`/§8; the concrete
`DiscordChannelEmitter` (the only module constructing `AllowedMentions`, `UNTRUSTED` default ⇒
`AllowedMentions.none()`) is the single emit seam.

### Not new forks — already-frozen owner-gated items this matrix confirms are still open
- **SF-a** panel-action grammar (route-through-C-1 vs panel-owned fields) — vocab §⑧; consumed
  fork-agnostically by `01` (P6 predicates), `02`, `06`, `10` (I-5 asserts the *step* exists, not the
  fork). No new disagreement.
- **SF-d** `SB_PROD_ATTEST` durable custody source — vocab §⑧ / `05 §9` / `12 CL-5b`. Consolidated into
  `12`'s registry row; the custody *source* stays owner-gated. No new disagreement.
- **SF-c** dispatch-trace audit promotion; **SF-e** durable cooldown store; **SF-f** rung-4 failure
  policy; **SF-g** store-drop disposition — all consumed to their frozen defaults across the set.

---

## 9. Reconciliations confirmed holding across the whole set (the RC ledger)

Every reconciliation the frozen vocab (`shared-vocabulary.md §⑨`) froze is **verified consistent** across
all 14 specs by this pass. RC-1…RC-15 were frozen at synthesis; **RC-16…RC-21 are this pass's additions**
(the two formerly-unnumbered "new" rows plus the four applied forks and the pending `ChannelEmitter` port).

| RC | Seam | Winner / loser-to-change | Status this pass |
|---|---|---|---|
| RC-1 | ① result grammar | outcome vocab = `contracts.py:48-52`; dispatch = `WorkflowResult\|None`; `StageResult` ≠ dispatch return | **holds** — 01/02/03/04/05/06/07/08/09/11/13 all cite the real seams |
| RC-2 | ② `AuthorityDecision` | 04's 10-field wins; **02 imports it** | holds; **02 (as written) still 5-field — must absorb** |
| RC-3 | ② `Lane` | 04's `Lane{CAPABILITY,TIER}` in `authority.py` wins; **02 drops `AuthorityLane`** | holds; **02 still `AuthorityLane` — must absorb** |
| RC-4 | ②/③ owner-override threading | resolver threads `owner_override` into channel-access; **02** | holds; **02 step-2 still independent — must absorb** |
| RC-5 | ②/③ transparency trigger | 04's `owner_override ∧ (lane_would_deny ∨ channel.would_deny…)`; **02** | holds; **02 must extend its trigger** |
| RC-6 | ① `DenialReason` home | `sb/spec/outcomes.py` leaf | **holds** — 04/07 import it; 02 §3.6 inline copy illustrative |
| RC-7 | ⑦.2 namespace oracle | **RESOLVED** — 01 adopted K1 `validate(snapshot)→NamespaceReport`, `(kind,value,scope)` key | **holds** — 01 §4.2/§10 reconciled |
| RC-8 | ① `DBUnavailable` | zero-edit via existing `ConnectionError` transient row | **holds** — 05 §3.9 |
| RC-9 | ⑤ drain-gate cite | `can_accept_commands()`/`is_shutting_down()` (K5); `/ready` RUNNING-only | **holds** — 02/05/08/09 |
| RC-10 | ⑦ config accessor | one typed attribute per field | **holds** — 05 in-file |
| RC-11 | ① / namespace `Surface` | **do NOT unify** the two `Surface` enums | **holds** — the background `MAINTENANCE` member (RC-19) is added to the **interaction** `Surface` (02), not the namespace one |
| RC-12 | ② `ActorRef.member_tier` | additive field on 02's `ActorRef` | holds; **02 must still add `member_tier`** (distinct from RC-18 `actor_type`, now applied) |
| RC-13 | ② `ChannelAccessDecision` | 04's **8-field** (`+detail`) wins | **holds** — 04 owns; consumers narrow to it |
| RC-14 | ② `denial_message` | engine-generated, not `[S]` | **holds** — 04 §3.3; 02's `from_exception` reads it |
| RC-15 | ②/③ transparency emit | `TransparencySink` port + trace flag, **not** `emit_audit_action` | holds; **02 must name `build_transparency_audit`+`TransparencySink`** |
| **RC-16** | ③ correlation | `audit_log.correlation_id` **column** (not a 12th bus field) | **RECONCILED across 06/07/08** — resolves 06 §12's open co-decision (formerly the unnumbered "new" row) |
| **RC-17** | ⑥ `DeliveryClass` home | `sb/spec/events.py` (07 imports; 08 owns) | **RECONCILED** — 08 §12.1 / 07 §8 fork F (formerly the unnumbered "new" row) |
| **RC-18** *(new, F-4)* | ② `ActorRef.actor_type` | additive `actor_type: str = "user"` (`{user,system,backfill,setup_delegate}`) on 02's `ActorRef` + vocab §⑩; K7 maps → `AuthorityRequest.actor_type` | **APPLIED 2026-07-04** — 02 §3.1 adds the field; 09 (`system`)/11 (`backfill`) consume; scripted-bypass drives off it |
| **RC-19** *(new, F-5)* | ① background `Surface` | ONE member `Surface.MAINTENANCE = "maintenance"` (scheduler fires AND sweep-repairs); `from_exception.target → TargetRef\|None` | **APPLIED 2026-07-04** — 02 §3.1/§3.3 define; 09 §3.8 / 11 §2.2/§4/§8.2 / 07 §3.3-4b adopt |
| **RC-20** *(new, F-1)* | ⑤/⑥ poll topology | **09 HOSTS** `OutboxRelayLane`+`OutboxReaperLane` as `PollLane`s on its one `PollSupervisor` at 5 s; roster non-exhaustive | **APPLIED 2026-07-04** — 09 withdraws the standalone-1 s model; 08 already host-citing |
| **RC-21** *(new, pending — Q-D26)* | ②/output-binding | the `ChannelEmitter` send-egress port + egress AST fence (concrete `DiscordChannelEmitter`, `UNTRUSTED` ⇒ `AllowedMentions.none()`) | **PENDING** — a 02/K8 seam correction registered here (was omitted from the reconciliation layer); parallel to RC-12/F-4; homed as Q-D26 in the register, `10 §2.A`/§8 |

**Pending-absorption summary.** Spec **`02` (resolver)** is written to its pre-hardening shapes and is
still the single loser-spec on **RC-2, RC-3, RC-4, RC-5, RC-12, RC-13, RC-14, RC-15** — the concentrated
authority-hardening edit the matrix surfaces, which a `02` revision must land before K8 builds, or L-12
(owner channel-deny) and the tier-lane re-open. *This pass narrowed that list by one:* **F-4/RC-18
(`actor_type`) is now applied to `02`'s `ActorRef`**; **RC-12 (`member_tier`) remains pending** (a
different additive field, deliberately out of this pass's scope). None of the pending rows is a
*disagreement* — the winners are frozen — but they are the one remaining concentrated `02` edit. The new
**RC-21 `ChannelEmitter` port** is a pending additive correction, not a `02`-absorption row.

---

*Synthesized 2026-07-04 over the frozen `shared-vocabulary.md` (all-five-pass) and all 14 design specs
read in full; **updated 2026-07-04** to record the four applied cross-strand reconciliations (F-1/F-2/
F-4/F-5) and carry F-3 to owner register PG-2. Cross-checked so the vocab wins where it reconciled a
disagreement. **NOT SOURCE OF TRUTH for runtime** — a design contract whose job is to prove the specs
agree on every recurring seam and to name the one that is still owner-gated.*
