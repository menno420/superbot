# Seam-Consistency Matrix — the 14 design specs against the 7 shared-vocabulary contracts

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
> **Headline result.** **56 of 61 touched cells AGREE.** The reconciled seams the vocab already froze
> (RC-1…RC-15) all hold across the whole set. **Five genuine open forks remain** — the biggest is a
> *direct contradiction* between `08` and `09` on where the outbox relay runs (each spec believes the
> other decided the opposite way). None blocks strand-2/3 from building to the frozen shapes; all five
> are register entries an owner or a vocab re-freeze closes.

---

## 0. The five open forks at a glance (read this first)

| # | Seam | Specs | The disagreement | Blocks a build? |
|---|---|---|---|---|
| **F-1** | ⑤ restart-safety / ⑥ delivery — **poll topology** | `08` ↔ `09` | `08` (as written) registers the relay as a **`PollLane` on `09`'s `PollSupervisor`** (5 s, no own loop); `09` (as written) says the relay is **its own supervised `RELAY_TASK(Interval 1s)`, "NOT my lane, I do not host it."** Each spec cites the other as having decided *its* way. The outbox ends up **unhosted** if both build as written. | **Yes** — contradictory ownership; one must be edited before wiring the composition root. |
| **F-2** | ① error-envelope — **`Surface` member for background fires** | `09`, `11` (touches `02`'s frozen `Surface`, RC-11) | `from_exception` needs a `surface`; a scheduler fire / sweep-repair has none. `09` proposes `surface="scheduler"`; `11 §4 Q4` flags `scheduler` vs a broader `maintenance` and refuses to fork it. The frozen interaction `Surface` carries **neither**. | No — additive enum member; both use `"scheduler"` for v1. |
| **F-3** | ③/④ — **K7 engine entry the draft consumes** | `06` ↔ `07` | `07 §3.2` provides `apply(op, *, conn)` (external-conn, **no EFFECT legs**) and names it "the draft-pipeline per-op apply (06 §3.5)". `06` (as written) **retired `apply(op)`**, uses **per-op `run(spec, ctx)`** (engine-owned txn, **runs** post-commit EFFECT legs — which its channel-create ops require), and states `run_ref` is "NOT in 07's declared API." `07` *does* declare `run_ref`. | **Yes** — 06 and 07 disagree on which entry the draft calls and whether resource-create EFFECT legs run. |
| **F-4** | ⑦ config/intent rail — **intent-denial posture** | `14` ↔ `05` | `05 §3.1` declares `message_content`/`members` **`required=True` ⇒ `FAILED_STARTUP`** on denial. `14 §2.B` flips them to **`required=False` + `IntentPosture.DEGRADE`** (boot slash-only). `14` routes this as a seam correction to `05` (**PG-2, owner-gated**). | No — owner-gated; `05`'s fail-closed floor is safe until flipped. |
| **F-5** | ② authority — **`ActorRef.actor_type`** | `09`, `11` assume it; vocab §⑩ / `02` lack it | `09`/`11`'s `SYSTEM_ACTOR`/`SWEEP_ACTOR` need `ActorRef.actor_type ∈ {system, backfill}` to drive K7's scripted-bypass. Frozen `ActorRef` (vocab §⑩) has no `actor_type`. Additive, like RC-12's `member_tier`. | No — mechanical additive field; needs a new RC entry. |

---

## 1. Seam ① — THE ERROR-ENVELOPE / `Result` GRAMMAR

**Canonical (vocab §① / §⑦.1 / §0, RC-1/RC-6/RC-8):** outcome vocab = the 5 real constants
`SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED` (`services/lifecycle/contracts.py:48-52`); dispatch
return = `WorkflowResult | None` (K7 **design** superset of `LifecycleResult`, no shipped class);
`StageResult` is the message-pipeline substrate, **never** a dispatch return; `from_exception` +
`ErrorClass{NONE,USER_ERROR,DENIED,TRANSIENT,BUG}` + `DenialReason` (leaf `sb/spec/outcomes.py`, RC-6);
`bug → BLOCKED` nuance lives in `error_class`+`reason`, never a 6th outcome.

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **02** | **OWNS** `from_exception`, `Result`, `ErrorEnvelope`, `ErrorClass`; leaf owns `DenialReason` | The frozen table (5 rows) → §2.7 outcomes; `Result.outcome` copies `WorkflowResult.outcome` through; `StageResult` dropped from the dispatch grammar (§3.6) | **AGREE** (RC-1 framing verbatim) |
| **01** | Consumes | `audit_completeness`/`never_strand` read the `WorkflowRef` return = `WorkflowResult\|None`; `core/contracts.py` re-confirmed absent | **AGREE** (RC-1 mis-cite fixed) |
| **03** | Consumes | trigger-set rejection ⇒ `outcome=BLOCKED` on the **real** `contracts.py:50` (§3.4) | **AGREE** |
| **04** | Consumes | denial ⇒ resolver maps to `BLOCKED`/`error_class=denied`; engine returns `allowed:bool`+`DenialReason` | **AGREE** |
| **05** | Consumes | `DBUnavailable(ConnectionError)` routes through 02's **existing** `ConnectionError` transient row → transient/`DISCORD_FAILED` (RC-8, zero-edit) | **AGREE** |
| **06** | Consumes | `from_exception(exc,surface,target,section_label)`; `DenialReason` incl. `CONFIRM_DECLINED`; op failures → §2.7 outcomes (§3.6 table) | **AGREE** |
| **07** | **OWNS** `WorkflowResult` (design superset) | copies outcome through; `ConfirmRequired` is a **control signal, NOT a `from_exception` input** (§3.3 step 2); error-**return** contract (catch+roll-back+return, never raise) | **AGREE** |
| **08** | Consumes | `WorkflowResult` design type; `outcome` values in `event_outbox` are the frozen 5 | **AGREE** |
| **09** | Consumes | classifies fire/compensation exceptions via `from_exception` with **`surface="scheduler"`** | **OPEN-FORK F-2** |
| **11** | Consumes | sweep-repair exceptions via `from_exception`; **reuses `surface="scheduler"`** but flags `scheduler` vs `maintenance` (§4 Q4) | **OPEN-FORK F-2** |
| **13** | Consumes | reads only `WorkflowResult.{outcome, mutation_id}` (design §2.7 fields) | **AGREE** |

*Cells: 9 AGREE · 2 OPEN-FORK (F-2).*

---

## 2. Seam ② — `authority_ref → LANE` (+ owner-override-once + channel-access + transparency)

**Canonical (vocab §② / §⑨ RC-2/3/4/5/12/13/14/15 · owner: `04`/K6):** one `authority_ref: str` on
**six** spec types; `classify_authority_ref → Lane{CAPABILITY,TIER}` (in `sb/spec/authority.py`, RC-3);
`AuthorityRequest` (discord-free, carries `member_tier`); `AuthorityDecision` **10-field** (04 owns; 02
imports — RC-2); `resolve_authority` owner-override-once-at-top; `ChannelAccessDecision` **8-field**
with `detail` (RC-13); `AccessMode` = shipped value strings; `denial_message` **engine-generated**
(RC-14); transparency rides **`TransparencySink` port + `command.dispatched` `override_applied` flag**,
**not** `emit_audit_action` (RC-15); `owner_override_holds(user_id,is_member)` the single predicate.

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **04** | **OWNS** all of the above | 10-field `AuthorityDecision`; `Lane{CAPABILITY,TIER}`; 8-field `ChannelAccessDecision(+detail)`; `AccessMode` shipped strings; `TransparencySink`; discord-free `AuthorityRequest.member_tier` | **AGREE** (owner) |
| **01** | Consumes | P4 calls `validate_authority_ref(ref)` on **six** spec types; `""`⇒ADMIN-floor always-valid; P3/P4 split | **AGREE** (RC-7 done) |
| **02** | Consumes (WRITTEN pre-hardening) | still carries `AuthorityLane{CONFIG_GOVERNANCE,DOMAIN}`, **5-field** `AuthorityDecision{allowed,lane,denial_copy,override_applied,base_allowed}`, `ActorRef` **without `member_tier`**, channel-access **not** threaded `owner_override`, transparency sink **unnamed** | **RECONCILED — 02 is the loser (RC-2/3/4/5/12/13/14/15); must absorb 04's shapes** |
| **03** | Consumes | P3 owns capability **format + reserved-prefix owner** (`{sub}.{res}.{action}`); P4 owns lane resolution — no overlap | **AGREE** |
| **06** | Consumes | `resolve_authority`, `AuthorityRequest`, 10-field `AuthorityDecision`, `owner_override_holds`; `resolve_draft_accept` = **AND over every distinct op `authority_ref`** | **AGREE** |
| **07** | Consumes | leg-0 `resolve_authority(AuthorityRequest(spec.authority_ref, actor…))`; reads `AuthorityDecision.{allowed,denial_message}`; passes `ctx.actor.member_tier` | **AGREE** |
| **09** | Consumes | scripted-bypass on `actor_type ∈ {system,backfill}`; `SYSTEM_ACTOR` needs **`ActorRef.actor_type`** (§12.1) | **OPEN-FORK F-5** (additive field) |
| **11** | Consumes | `SWEEP_ACTOR.actor_type="backfill"`; **consumes** 09's `ActorRef.actor_type` correction (does not re-flag) | **OPEN-FORK F-5** |
| **14** | Consumes | invoker `member_tier` computed from the `INTERACTION_CREATE` payload (needs no privileged intent); shape ②/RC-12 | **AGREE** |
| **10** | Consumes (asserts) | class-13 owner axis **asserts** the single `is_platform_owner` AST fence + `TransparencySink` (RC-15) exist | **AGREE** |

*Cells: 7 AGREE · 1 RECONCILED (02) · 2 OPEN-FORK (F-5, additive).*

---

## 3. Seam ③ — AUDIT-ROW SEMANTICS + `mutation_id`

**Canonical (vocab §③ · owners: shipped `emit_audit_action` 11-field → K7; dispatch-trace `02`;
`audit_log` central row `07`; durable twin `enqueue_audit_action` `08`):** **one dispatch-trace +
zero-or-more mutation-audit rows per command**; mutation audit = the frozen **11 keyword-only fields**
keyed by `mutation_id` (pipeline UUID, the link between `audit.action_recorded` and the DB row);
single-op ⇒ 1 row, batched lifecycle op ⇒ **1** row, compound draft ⇒ N rows correlated by a shared
id. Transparency notice is **neither** seam (RC-15). Correlation is a **`audit_log.correlation_id`
column**, never a 12th bus field (07 §5 / 08 §5.1 / 06 §12 — **RECONCILED**).

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **07** | **OWNS** `audit_log` central row + `correlation_id` column + `emit_central_audit` over the durable twin | one `audit_log` row per invocation, `mutation_id` PK, legs as `detail` JSONB, `correlation_id=ctx.correlation_id`; never N rows | **AGREE** (owner) |
| **02** | **OWNS** the dispatch-trace | `command.dispatched` `EventSpec(observability_only=True, owner_subsystem="kernel")`; `override_applied`/`base_allowed` **derived** from `AuthorityDecision`; never bypasses `emit_audit_action` | **AGREE** (derived-flag shapes per RC-2/5/15) |
| **01** | Consumes | P6 `audit_completeness`: `effect="mutating"` ⇒ MUST carry a `WorkflowRef` (compile proxy for "routes through `emit_audit_action`") | **AGREE** |
| **04** | Consumes | `TransparencyAudit` does **NOT** fill the 11-field seam; rides `TransparencySink` + the trace flag (RC-15) | **AGREE** |
| **05** | Consumes | `idempotency_keys.result_ref` points to the audit/mutation id | **AGREE** |
| **06** | Consumes | `ctx.correlation_id = draft_id` written to each op's `audit_log.correlation_id`; **one** central row per op; the 11-field bus payload unchanged | **AGREE** (correlation-by-column reconciled) |
| **08** | **OWNS** `enqueue_audit_action(conn, **11 fields)` durable twin | delivers the byte-identical `audit.action_recorded`; adds the `correlation_id` column | **AGREE** |
| **09** | Consumes | fire's mutation audits **inside** `run_ref`'s central row on my conn; due-queue arm/claim/fire bookkeeping is **not** an auditable mutation | **AGREE** |
| **10** | Consumes | `erasure_ref` = `WorkflowRef` ⇒ one `emit_audit_action` per store; bare `HandlerRef` erasure = `SEMANTIC_VIOLATION` (reuses §③.4) | **AGREE** |
| **11** | Consumes | repair = `WorkflowRef` central row `mutation_type="invariant_repair:<id>"`; `sb_invariant_sweep_log` is kernel-internal, **not** audited | **AGREE** |
| **13** | Consumes | reverse-import LEDGER tier re-inserts by `mutation_id` `ON CONFLICT DO NOTHING`; notes `audit_log` is the **forensic** substrate, not a complete money log (legacy hole closed for new-bot by §③.4) | **AGREE** |

*Cells: 11 AGREE. No divergence — the correlation-id-by-column reconciliation holds across 06/07/08.*

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
| **06** | Consumes (via K7) | `dedup_token = f"{draft_id}:{op_seq}"` supplied to K7's per-op `once()` (completes §④.2) | **AGREE** |
| **07** | Consumes | `DedupKeySpec`; `DURABLE_ONCE ⇒ once()+record_outcome` namespace=`op_key`; farm-collect `dedup_key=(user_id,interaction_id)` (cross-user-safety) | **AGREE** |
| **08** | Consumes | outbox `dedup_key` **IS** `IdempotencyKey.render()`; `UNIQUE(dedup_key)` = the exactly-once capture; per-producer disambiguator `…:{event_name}`/`…:{emit_index}` | **AGREE** |
| **09** | Consumes (+adds 4th site) | fire `dedup_token=f"{task_id}:{fire_epoch}"` **deterministic** (fixes the shipped uuid4); version-reject `{table}.version_reject:{…}` | **AGREE** |
| **11** | Consumes (+adds 5th/6th) | cadence `{invariant_id}.sweep:{epoch}` + repair `{invariant_id}.repair:{row_id}:{fingerprint}`; §8.1 flags §④.2 non-exhaustive | **AGREE** (additive) |
| **12** | Consumes | rotation `once(IdempotencyKey("credential.rotation", 0, f"{name}:{horizon_epoch}"))` | **AGREE** (additive site) |
| **13** | Consumes | reverse-import ledger by `mutation_id` PK; `once()`-tied | **AGREE** |
| **14** | Consumes | `platform.guildcap` latch (or a settings row) for the ~75/90 fire-once | **AGREE** |

*Cells: 10 AGREE. The additive-sites note is a completeness annotation, not a shape divergence.*

---

## 5. Seam ⑤ — THE RESTART-SAFETY PATTERN

**Canonical (vocab §⑤ · owners `05` durable store + drain gate, `09` scheduler completer):** durable
state in DB tables (not memory); **drain gate** at resolver step 0 (`can_accept_commands()`; RC-9);
**boot-reconcile fires overdue exactly once, after `/ready` 200 = RUNNING** (RUNNING-only, STARTING⇒503,
05 §3.8); **fast-release handoff** covered by `once()`+`db.transaction()` uniformly. The shared poll host
is `09`'s `PollSupervisor` + `PollLane` port.

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **05** | **OWNS** the store + drain gate + `/ready` | `/ready` RUNNING-only 200; fast-release releases the lock immediately; `once()` covers the overlap | **AGREE** (owner) |
| **09** | **OWNS** scheduler completion | durable `sb_due_queue`; boot-reconcile after RUNNING (bounded `claim_due` SKIP-LOCKED loop); `PollSupervisor`+`PollLane`; `SYSTEM_ACTOR` | **AGREE on skeleton; OPEN-FORK F-1 on who hosts the outbox** |
| **02** | Consumes | step-0 drain gate `can_accept_commands()` on **every** surface (RC-9); confirmations survive nothing | **AGREE** |
| **06** | Consumes | drafts durable; **no** auto-apply on boot; `ExpiryJanitorLane` + stuck-`APPLYING` sweep on **09's** `PollSupervisor` | **AGREE** |
| **07** | Consumes | stateless; arms no timers; **no** boot-reconcile (supplies the `run_ref` substrate the scheduler fires through) | **AGREE** |
| **08** | Consumes | relay `reconcile_on_boot` = **no-op** (first post-RUNNING tick IS the reconcile); supervisor gates on RUNNING first | **OPEN-FORK F-1** (hosting) |
| **11** | Consumes | `InvariantSweepLane` a `PollLane` on **09's** supervisor; cadence via `{invariant_id}.sweep:{epoch}` `once()`; `reconcile_on_boot` re-runs incomplete epochs | **AGREE** (consistent with 08's registered-lane model) |
| **12** | Consumes | rotation read-back waits for `/ready` 200 (post-boot instance); `once()`+boot-reconcile guards double-issue | **AGREE** |
| **13** | Consumes | `SB_VERIFY_BOOT` **suppresses** boot-reconcile + relay (T-7); requires `SB_DATA_PLANE=test` | **AGREE** (contained) |
| **14** | Consumes | `platform.guildcap.<t>` durable fire-once latch, restart-safe | **AGREE** |

*Cells: 8 AGREE · 2 OPEN-FORK (F-1: 08 and 09 contradict on relay hosting).*

---

## 6. Seam ⑥ — `EventSpec.delivery` (durable delivery)

**Canonical (vocab §④/§⑤ skeleton · owner `08`):** `DeliveryClass{AT_LEAST_ONCE, BEST_EFFORT}` **home =
`sb/spec/events.py`** (07 imports it, no local copy — RC per 08 §12.1 / 07 §8 fork F); `EventSpec.delivery`
[S] default `BEST_EFFORT`; `AT_LEAST_ONCE` ⇒ in-txn `event_outbox` row + post-commit relay; the outbox
`dedup_key` is an `IdempotencyKey.render()`; `enqueue_all(emits, ctx, result, *, conn) -> BestEffortBatch`.

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **08** | **OWNS** `DeliveryClass` + `EventSpec.delivery` + `event_outbox` + relay | canonical enum home; `enqueue`/`enqueue_all`/`enqueue_audit_action`; exactly-once-capture / at-least-once-relay / handler-dedup contract | **AGREE on the grammar; OPEN-FORK F-1 on the relay's runtime host** |
| **07** | Consumes | **imports** `DeliveryClass` from `sb/spec/events.py`; `EventEmitSpec.delivery`; `enqueue_all` in-txn at step 4 + `emit_after_commit()` at step 6 | **AGREE** (RC — one enum, no drift) |
| **05** | Consumes | `observability_only=True ⇒ delivery==BEST_EFFORT` (the compile fence) | **AGREE** |
| **06** | Consumes | `AT_LEAST_ONCE` emits via K7's `enqueue_all` on the op txn | **AGREE** |
| **09** | Consumes/relates | the outbox `RELAY_TASK` is written in **09's** `ManagedTaskSpec` durability grammar — **but 09 models it as its own supervised `Interval(1s)` task** | **OPEN-FORK F-1** |
| **11** | Consumes | Discord output from a sweep-repair = an `AT_LEAST_ONCE` outbox emit on the sweep conn (never a post-commit EFFECT leg) | **AGREE** |
| **13** | Consumes | scheduled Discord output rides an `AT_LEAST_ONCE` outbox emit | **AGREE** |

*Cells: 6 AGREE · 1 OPEN-FORK (F-1, cross-listed with ⑤).*

---

## 7. Seam ⑦ — CONFIG / SECRET GRAMMAR + THE DATA-PLANE RAIL

**Canonical (vocab §⑥ · owner `05`):** `ConfigSpec`/`SecretSpec`/`ConfigPosture`/`ConfigType`(+CSV)/
`IntentSpec`; one typed frozen `Config` attribute per field (verbatim env name, RC-10); `parse_bool` the
one grammar; `preflight()` first in the composition root; `assert_data_plane` the 4th rail (non-`test`
DSN ⇒ `RefuseBoot`); `CONFIG_FIELDS = 47`; `INTENT_CONTRACT` (`message_content`/`members`, both
privileged, **`required=True`**).

| Spec | Owns/Consumes | Exact shape it uses | Verdict |
|---|---|---|---|
| **05** | **OWNS** the grammar + rail + `INTENT_CONTRACT` | `CONFIG_FIELDS` (47); `assert_data_plane`; `SB_PROD_ATTEST` presence-gated `SecretSpec`; `message_content`/`members` `required=True` fail-closed | **AGREE** (owner) |
| **12** | Consumes | **`CredentialSpec` a SIBLING leaf** (`sb/spec/credentials.py`) — does **not** mutate `SecretSpec`/§6.1; `config_ref` names the `SecretSpec.env_var`; consumes the data-plane rail | **AGREE** (sibling-leaf discipline, no §6.1 amendment) |
| **13** | Consumes (+adds) | `SB_VERIFY_BOOT: BOOL` = an **additive 48th** operational `ConfigSpec` (§8.5 flags "47 total" not closed); `SB_DATA_PLANE=test` forced for verify | **AGREE** (additive; vocab count 47→48 to absorb) |
| **14** | Consumes (+corrects) | extends `IntentSpec` with `IntentPosture`+`degrades`; **flips `message_content`/`members` `required=True → False` + `posture=DEGRADE`** (PG-2 seam correction to `05`) | **OPEN-FORK F-4** (owner-gated) |
| **10** | Consumes (asserts) | class-13 asserts no un-redacted `SecretSpec` on any log/`/metrics`/diag path (`SecretSpec.redact`, 05 §3.2/3.8) | **AGREE** |
| **11** | Consumes | `INVARIANT_ENFORCE(id)` `settings_keys` constant via the config/settings rail (never `os.getenv`) | **AGREE** |

*Cells: 5 AGREE · 1 OPEN-FORK (F-4). Plus two additive-not-fork notes: `SB_VERIFY_BOOT` (47→48) and the
existing owner-gated **SF-d** `SB_PROD_ATTEST` custody source (12 CL-5b) — both already tracked, neither
new.*

---

## 8. Disagreements + open forks (every non-AGREE cell, with what must change)

### F-1 — Poll topology: where does the outbox relay run? (`08` ↔ `09`) — **DIRECT CONTRADICTION**
- **`08` (as written)** — `§3.4`, `§8 fork G (ii)`, `§12.4`: "The relay is **not** a standalone loop. It
  is an `OutboxRelayLane` **registered on the scheduler's shared `PollSupervisor`**"; the composition
  root calls `supervisor.register_lane(OutboxRelayLane(...))` + `register_lane(OutboxReaperLane(...))`;
  `reconcile_on_boot` is a **no-op**; cadence = the supervisor's `poll_interval_s=5` (deferral 2). `08`
  cites *"09 §8 closed 'one PollSupervisor, registered lanes' over '3 loops'."*
- **`09` (as written)** — `§3.6`, `§8 poll-topology (b)`, `§11`, `§12.4`: "The outbox `RELAY_TASK` is
  **NOT** registered here — it is ⑥'s **own** supervised `ManagedTaskSpec(Interval 1s)`… **I do NOT host
  or boot-reconcile it.**" `09` cites *"08 §3.4 models the relay as its OWN `RELAY_TASK`… self-reconciling."*
- **Why it's a real fork:** each spec asserts the **other** decided the opposite. `08` (later, more
  detailed) builds a `PollLane` and expects `09`'s supervisor to host it; `09` refuses to host it and
  points at a standalone `RELAY_TASK(Interval 1s)` that `08` **does not define**. Built as written, the
  relay is **unhosted** (09 won't register it; 08 ships no standalone loop), and the cadence is
  ambiguous (5 s vs 1 s). `09`'s own supervisor lane-roster ("due-queue + draft janitor") is also stale
  vs what `08` **and** `11` register on it.
- **To close (recommendation):** adopt **`08`'s model** — `OutboxRelayLane` + `OutboxReaperLane` are
  `PollLane`s on `09`'s `PollSupervisor` at the 5 s cadence (matches the "one supervisor, registered
  lanes" principle `09` itself endorses for its other lanes, and `08`'s `AT_LEAST_ONCE`/audit latency
  tolerates 5 s). **`09` must edit `§3.6`/§11/§12.4** to (a) host the two outbox lanes, (b) drop the
  "own `RELAY_TASK` / `Interval(1s)` / not-my-lane / self-reconciling" language, and (c) make its
  lane-roster non-exhaustive (due-queue + draft janitor + **outbox relay/reaper** + **invariant sweep**).
  Register as a vocab reconciliation (poll-topology seam) so no third consumer re-derives it.

### F-2 — `from_exception` `Surface` member for background fires (`09`, `11`; touches `02`/RC-11)
- **The gap:** `from_exception(exc, *, surface, target)` requires a `surface`, but a scheduler fire /
  invariant sweep-repair has no interaction origin. The frozen interaction `Surface` (RC-11) =
  `{SLASH, PREFIX, COMPONENT, MODAL, NL_INTENT, NL_ORCHESTRATION}` — no background member.
- **`09`** uses `surface="scheduler"` ("a new `Surface` member is optional-additive"). **`11 §4 Q4`**
  reuses `"scheduler"` for v1 but explicitly **refuses to introduce a competing `"maintenance"`** and
  flags that a broader rename must be frozen for *both* siblings at once — i.e. the member is genuinely
  undecided.
- **To close:** a **vocab decision** — add **one** background `Surface` member (recommend a single
  `MAINTENANCE` covering scheduler fires *and* sweep repairs, or bless `"scheduler"` for both), frozen
  once. Additive to `02`'s enum; not owner-gated but must not be answered twice with two strings (that is
  the exact drift the vocab exists to kill). Register as a small RC.

### F-3 — K7 engine entry the draft pipeline consumes (`06` ↔ `07`)
- **`07 §3.2`** provides **three** entries — `run()` (engine-owned txn, runs EFFECT legs post-commit),
  `run_ref(ref, ctx, *, conn)` (external-conn, **no** EFFECT legs), `apply(op, *, conn)` (external-conn,
  no EFFECT legs) — and names **`apply(op, conn)` "the draft-pipeline per-op apply (06 §3.5 step 4)"**;
  fork A says the external-conn seam "lets the draft run N legs in one shared txn."
- **`06` (as written)** **retired `apply(op)`** ("There is no `engine.apply(op)`"), uses **per-op
  `run(spec, ctx)`** (each op its own txn; **resource-create channel ops run as post-commit EFFECT
  legs**, which it requires), explicitly **abandons** the cross-op shared-txn ("unachievable… retired"),
  and states `run_ref` is **"NOT in 07's declared API"** — but `07` *does* declare `run_ref`.
- **Why it's a real fork:** (a) 07 says `apply(op)` exists and is the draft's entry; 06 says it doesn't
  and uses `run()`; (b) 07's `apply`/external-conn runs **no** EFFECT legs, so the draft's channel
  creates **cannot fire** under it — 06's `run()` choice is the *technically correct* one; (c) 06's map
  of 07's API (`run()`/`preview()` only, no `run_ref`/`apply`) is **stale** vs 07-as-written. The two
  specs disagree on both the entry name and whether the batch is one shared txn or per-op.
- **To close (recommendation):** reconcile toward **06's semantics** — draft resource-create ops use
  **`run()`** (own txn + EFFECT legs), draft is **sequenced + per-op-atomic + idempotent-resume**, not
  one shared txn. **`07` must** stop naming `apply(op, conn)` "the draft entry" (or restrict it to
  pure-DB-only draft ops) and drop the fork-A claim that the draft runs N legs in one shared txn; **`06`
  must** update its "07's declared API" text to acknowledge `run_ref`/`apply` now exist (used by `09`/
  the scheduler, not by the draft's EFFECT-bearing ops). Register as a strand-2 co-decision.

### F-4 — Intent-denial posture: `required=True` fail-closed vs `DEGRADE` (`14` ↔ `05`)
- **`05 §3.1`** declares `message_content`/`members` **`required=True`**; `assert_intents` accrues a
  `ConfigError → StartupError → FAILED_STARTUP` when an unapproved privileged intent is missing in a
  non-`test` plane — **the bot refuses to boot**.
- **`14 §2.B`** flips both to **`required=False` + `IntentPosture.DEGRADE`** (+ `degrades` set), so
  denial **boots slash-only** with an explicit `DegradedCapability` notice; adds the enforced invariant
  `required == (posture is REQUIRED)`. `14` routes this as a **seam correction to `05`**, **owner-gated
  PG-2** (it flips a frozen `INTENT_CONTRACT` field).
- **To close:** **owner call PG-2.** Recommendation (14's): adopt `DEGRADE` — fail-closed darks the whole
  bot when it could serve every slash command, and slash-first survivability is the growth posture. The
  fail-closed floor (`05`) is safe until the owner flips it. Register as a router DISCUSS Q; `05 §3.1`
  gains `IntentPosture`/`degrades` and the mirror-invariant once approved.

### F-5 — `ActorRef.actor_type` additive field (`09`, `11` assume it; vocab §⑩ / `02` lack it)
- **The gap:** the frozen `ActorRef` (vocab §⑩) = `{user_id, is_guild_operator, is_bot_owner, is_dm,
  member_tier}` — **no `actor_type`**. But `09`'s `SYSTEM_ACTOR` (`actor_type="system"`) and `11`'s
  `SWEEP_ACTOR` (`actor_type="backfill"`) need it so K7 can map `AuthorityRequest.actor_type =
  ctx.actor.actor_type` and hit `resolve_authority`'s scripted-bypass (§②.3). `11` **consumes** 09's
  flag without re-flagging.
- **Why it's here (not just AGREE):** it is a real cross-spec assumption the frozen vocab does not yet
  carry — exactly the RC-12 `member_tier` situation one step later.
- **To close (recommendation):** **mechanical, not owner-gated** — add `actor_type: str = "user"` to
  `ActorRef` in `sb/spec`/`02`'s leaf and to vocab §⑩'s `ActorRef` line; K7 maps it into
  `AuthorityRequest`. Register as a **new RC** (additive field, winner determined) so both `09` and `11`
  stop carrying it as a flagged correction.

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

Every reconciliation the frozen vocab (`shared-vocabulary.md §⑨`) already froze is **verified consistent**
across all 14 specs by this pass:

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
| RC-11 | ① / namespace `Surface` | **do NOT unify** the two `Surface` enums | **holds** — 14 reads K1 `Surface==SLASH`, not the interaction enum |
| RC-12 | ② `ActorRef.member_tier` | additive field on 02's `ActorRef` | holds; **02 must add member_tier** (+ see F-5 `actor_type`) |
| RC-13 | ② `ChannelAccessDecision` | 04's **8-field** (`+detail`) wins | **holds** — 04 owns; consumers narrow to it |
| RC-14 | ② `denial_message` | engine-generated, not `[S]` | **holds** — 04 §3.3; 02's `from_exception` reads it |
| RC-15 | ②/③ transparency emit | `TransparencySink` port + trace flag, **not** `emit_audit_action` | holds; **02 must name `build_transparency_audit`+`TransparencySink`** |
| **new** | ③ correlation | `audit_log.correlation_id` **column** (not a 12th bus field) | **RECONCILED across 06/07/08** — resolves 06 §12's open co-decision |
| **new** | ⑥ `DeliveryClass` home | `sb/spec/events.py` (07 imports; 08 owns) | **RECONCILED** — 08 §12.1 / 07 §8 fork F |

**Pending-absorption summary:** spec **`02` (resolver)** is written to its pre-hardening shapes and is the
single loser-spec on **RC-2, RC-3, RC-4, RC-5, RC-12, RC-13, RC-14, RC-15** (plus F-5 `actor_type`). None
is a *disagreement* — the winners are frozen — but a `02` revision must land them before K8 builds, or
L-12 (owner channel-deny) and the tier-lane both re-open. This is the one concentrated edit the matrix
surfaces.

---

*Synthesized 2026-07-04 over the frozen `shared-vocabulary.md` (all-five-pass) and all 14 design specs
read in full. Cross-checked so the vocab wins where it reconciled a disagreement. **NOT SOURCE OF TRUTH
for runtime** — a design contract whose job is to prove the specs agree on every recurring seam and to
name the five that do not yet.*
