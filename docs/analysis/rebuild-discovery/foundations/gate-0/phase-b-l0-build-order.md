# Phase-B L0 build order — the authoritative 16-step (S0–S15) sequence

> **Status:** `reference` — **NOT SOURCE OF TRUTH.** The consolidated, ratified Gate-0 plan that the
> **later, separate new-repo Phase-B L0 build** executes. It freezes the dependency-ordered build of the
> 14 foundational design specs into the `sb/` package (which does **not** yet exist). It is a
> **specification, not code**.
>
> **Provenance / precedence (Q-0120 — source wins):** consolidated 2026-07-04 from Part 3 of
> [`docs/planning/rebuild-gate0-worklist-2026-07-04.md`](../../../../planning/rebuild-gate0-worklist-2026-07-04.md),
> **verified edge-by-edge** against the 14 specs' **§11 build-order** sections and the applied
> reconciliations in
> [`../design/seam-consistency-matrix.md`](../design/seam-consistency-matrix.md)
> (**F-1 / F-2 / F-4 / F-5 RESOLVED-and-applied; F-3 OPEN → owner register PG-2**). The 14 specs win
> for any shape they own; the frozen
> [`../design/shared-vocabulary.md`](../design/shared-vocabulary.md) wins where it reconciled a
> two-spec disagreement (the `RC-*` ledger). This plan adds **no** new ordering decision — it sequences
> what the specs already pin.
>
> **One verification correction folded in (see §7):** spec `02 §11` places its own `outcomes.py` leaf at
> **K7**; spec `04 §11` **recommends** landing that leaf one band earlier at **K6** so the authority
> engine need not forward-reference K7. This plan adopts **04's K6 recommendation** — it is the earlier,
> cycle-breaking placement and both specs agree the leaf is pure and may precede. This is the single edge
> where two specs' §11 sections differ; **04 wins** (the safe-earlier placement), 02's resolver still
> lands at K8.

---

## 1. Dependency-graph summary

1. **Strand 1 is a near-linear chain** `K0 → K1 → K2 → K3 → K4 → K5 → K6 → K7 → K8`, and it is the whole
   substrate. **01 (the K2 compiler) is the linchpin** — the snapshot is the spine *everything* declares
   into (K3 db, K4 events, K5–K10, all Phase-4 ports), and 01's P3 is *literally a call into K1's
   `validate` (RC-7)* — so **K1 (03) must precede K2 (01)** even though 01 is the headline build.
2. **05 is the floor; 05 + 04 are the strand-2 substrate.** 05's **K0 config** + **K3
   `IdempotencyKey`/`once()`/`db.transaction()`** and 04's **K6 authority contracts**
   (`resolve_authority`, `AuthorityDecision`) are what every strand-2 durability port stands on. **07
   (K7) is the strand-2 keystone** — it underlies 06 (draft) *and* 09 (scheduler); **08 (K4 outbox)**
   provides the durable delivery/audit twin they all emit through.
3. **Two apparent cycles are broken by the leaf/kernel split + the "armed-later" pattern — no true
   circular dependency exists.**
   - **(a) 02 ↔ 07:** 02's *pure leaf* `outcomes.py` (`from_exception`/`Result`) lands early at **K6** so
     07 can consume it at K7, while 02's *resolver* lands late at **K8** and consumes 07. Splitting the
     leaf from the resolver removes the cycle.
   - **(b) 08 ↔ 09:** 08 is *authored* at **K4** but its relay/reaper lanes are only *registered*
     (composition-root) at/after **K5** on **09's** `PollSupervisor` (F-1/RC-20); 08's enqueue/store
     depend on K3, not on 09. The "authored-early / registered-later" pattern removes the cycle.
4. **Strand 3 (10–14) rides the frozen grammar.** It consumes the frozen vocab + K7 `run_ref` + 09's
   `PollSupervisor` + the Gate-0 grammar leaves, adds **no** new kernel ordering, and can build in
   parallel once K7/K9 exist and the grammar is frozen.
5. **The one contested/open edge is F-3** — 14's `IntentPosture=DEGRADE` + `required=False` seam
   correction to 05's `IntentSpec`. It is **owner-gated, carried to register PG-2, NOT closed by edit**;
   every other cross-spec fork (F-1/F-2/F-4/F-5) is RESOLVED-and-applied in-spec.

**K-band legend (design-spec §9.1):** `K0` config/observability substrate · `K1` namespace registry ·
`K2` manifest compiler + snapshot · `K3` db + idempotency seam · `K4` event outbox · `K5` lifecycle +
health + poll host · `K6` authority engine · `K7` workflow/compound-op engine · `K8` interaction runtime
(resolver) · `K9` strand-2 durability band (draft + due-queue) · `K10` reserved. "Arms later" = a
contract *defined* at one slot that *activates* when a later input lands.

---

## 2. The sequenced L0 build-order table (16 steps, S0–S15)

Specs **01, 05, 09, 02** each span **>1 K-slot**; those rows note the split. "Applied reconciliations"
names the seam-matrix `RC-*` / `F-*` fixes already in-spec that the step must build to.

| # | K-slot | Spec(s) | PROVIDES (what it lands) | CONSUMES (upstream deps) | Applied seam reconciliations |
|---|---|---|---|---|---|
| **S0** | pre-Gate-0 | **01 §3.7** | `docs/planning/rebuild-amendments.yml` (sole amendment-ID minting authority) + `tools/check_amendments.py` (required check) | — (docs/tooling leaf) | — (built **before** the Gate-0 fold so G-9…G-24 stamp `in-spec` off a collision-free list). **Blocks:** Gate-0. |
| **S1** | **K0** | **05** (config / observability / intents leg) | `sb/spec/config.py` + `sb/kernel/config` (`preflight()→Config`, `parse_bool`/`parse_dsn`); `sb/spec/observability.py` + metrics `render()`; `IntentSpec` + `assert_intents`; checkers `check_config_usage` / `check_metric_cardinality` | — (substrate; runs first at boot) | RC-10 (one typed attribute per field). **Blocks everything** — the composition root cannot boot without the config object; `db.init(cfg)` takes it; intents gate gateway connect. |
| **S2** | **K1** | **03** (namespace registry) | `namespace.validate(snapshot)→NamespaceReport`; `is_reserved(value,kind,*,surface,parent)`; `Collision(kind,value,scope,claimant_a/b)`; tombstones + `legacy_reservations.json`; cap guard; `check_namespace` + symbol-shadow AST pass | **K0** only (K1 is a leaf) | RC-7 (its `validate` **is** 01's P3). Pre-K2 one-time `tools/compute_corpus.py` runs at **Stage-2**. **Blocks** K2/K6/K8 + the invocation subsystem. |
| **S3** | **K2** | **01** (compiler / snapshot / amendments) — **THE LINCHPIN, first real build** | `tools/manifest_compile.py` (9 passes P1–P9 + `_project`); `sb/spec/refs.py` (`*Ref` + `@handler` dup-guard `RefRedefined`) + `roles.py`; `manifest.snapshot.json` serializer + `stable_hash`; failure taxonomy; `sb/app/boot_gate.py` leg-A recompile-parity; arrangement-invariance test | **K1** (P3 = calls K1's `validate`; both surfaces node shape) | **RC-7** (P3 ≡ K1's `validate`). Arms-later: **P7** store-completeness arms at **K3**; **leg-B** build-parity + **leg-C** remote-parity arm at **K8**. **Blocks K3–K10 + all of Phase 4.** |
| **S4** | **K3** | **05** (db seam leg) | `sb/kernel/db/{pool(+transaction),data_plane,migrations,idempotency}` — `db.transaction()`, `assert_data_plane()` (the 4th rail), fresh migration runner + `verify_applied_checksums`, `IdempotencyKey`/`once()`/`record_outcome`; `check_migrations` | **K0** (`db.init(cfg)`) | Seam ④ owner. **The strand-2 substrate primitive** — `once()`/`db.transaction()` consumed by 06/07/08/09 (transitively via K7). Arms 01's **P7** store-completeness. |
| **S5** | **K4** | **08** (event outbox) | `sb/spec/events.py` (`DeliveryClass{AT_LEAST_ONCE,BEST_EFFORT}` — **canonical enum home**, K7 imports it) + `EventSpec.delivery` [S]; `event_outbox` table + atomic claim; `enqueue`/`enqueue_all`/`enqueue_audit_action` (durable audit twin); `delivery_declared` fence | **K3** (`db.transaction()`, `IdempotencyKey`) + `sb/spec/events.py` | **RC-17** (`DeliveryClass` home = `sb/spec/events.py`, no local K7 copy). Relay/reaper lanes **authored** here, **registered at/after K5** on 09's `PollSupervisor` (**F-1/RC-20**). Provides K7's step-4e `enqueue_all` + step-6 `emit_after_commit()`. |
| **S6** | **K5** | **05** (health leg) + **09** (PollSupervisor host leg) | **05:** `sb/adapters/http/health.py` (`/ready`+drain, `/metrics` route), lifecycle STARTING/RUNNING. **09:** spawns the one supervised `PollSupervisor` + RUNNING/drain predicates. **Register 08's `OutboxRelayLane`+`OutboxReaperLane` here.** | **K3** (db) + **K4** (outbox lanes to register) | **F-1/RC-20** (09 hosts the outbox relay/reaper on its single supervisor at 5 s), **RC-9** (`/ready` RUNNING-only, `can_accept_commands()` drain gate). 09 has **two landing points** — poll host at K5, due-queue at K9-peer (S10). Readiness gates CUT-1. |
| **S7** | **K6** | **04** (authority engine) **+ 02's `outcomes.py` leaf (K6 per 04's recommendation)** | `sb/spec/authority.py` (`validate_authority_ref`, `classify_authority_ref` total/non-overlapping, tier order); `kernel/authority/{owner,decision,resolve,channel_access,transparency}.py`; 10-field `AuthorityDecision`; owner-override-once; `TransparencySink`. Landing `sb/spec/outcomes.py` (`from_exception`/`Result`/`ErrorClass`/`DenialReason`/`ReplyVisibility`/`DeferMode`) here lets authority avoid forward-referencing K7. | **K1** (capability reservation) + **K3** (revoke overlay / policy reads) + **K5** (admission sheds lifecycle/DM legs) | **RC-2/3/6/13/14/15** (04 owns the 10-field decision, `Lane`, `DenialReason` home, `+detail` channel access, engine-generated `denial_message`, `TransparencySink`). **Arms 01's P4** as soon as `validate_authority_ref` exists. **Blocks K7 + K8 + all Phase-4 mutations.** *(Leaf-at-K6 = 04's §11 recommendation over 02 §11's K7 — see §7.)* |
| **S8** | **K7** | **07** (workflow / compound-op engine) — **strand-2 keystone** **+ 02's `WorkflowResult`/`from_exception` grammar finalized** | `sb/spec/outcomes.py` finalized + `WorkflowResult`/`MutationPreview`/`StepResult`; `LegSpec`/`CompoundOpSpec`/`IdempotencyPosture`/`WorkflowContext`/`WorkflowRegistry`; **`run()`/`run_ref(conn=)`/`apply(op,conn)`/`preview()`** over one `_execute` core; central `audit_log` row via `enqueue_audit_action`; fences `idempotency_posture_declared`/`audit_completeness`/`atomic_db_only` | **K1,K2,K3,K4,K5,K6** (only layers above it) | **F-2 (PIN-2)** applied: `atomic_db_only` scope dropped the "…or a draft `op_kind` mapping" clause, so EFFECT-bearing draft ops go through `run(spec,ctx)` per-op; `run_ref`/`apply` fenced to **pure-DB external-conn callers only** (10-channel canary un-blocked). **RC-19** (K7 leg-exception path → `from_exception(exc, surface=MAINTENANCE, target=None)`). `WorkflowContext` gains `correlation_id`/`test_mode`/`actor_type` mapping. **Underlies 06 AND 09.** |
| **S9** | **K8** | **02** (C-1 resolver + error envelope) **+ THE SPEC-02 ABSORPTION EDIT** | `resolve()` single seam + `ResolveRequest`; `SurfaceResponder` port; 6 surface adapters (slash/prefix/fuzzy/component/modal/nl); `predicates.evaluate`; `from_exception`/`ErrorEnvelope`/reply-visibility/drain gate; `tree.error`/`on_app_command_error`. **AST no-skip fence arms here.** | **K1** (name resolution) + **K5** (admission) + **K6** (`authority_ref`→`AuthorityDecision`) + **K7** (`Result`/audit spine) | **EXPLICIT L0 ABSORPTION TASK:** 02 is written to pre-hardening shapes and must absorb 04's frozen authority contracts **RC-2/3/4/5/13/14/15** + thread `owner_override` into channel-access + name the `TransparencySink` seam **before K8 wires up**. **F-4/RC-18 (`actor_type`) already landed** on 02's `ActorRef`; **RC-12 (`member_tier`) still PENDING** in this batch. **Arms 01's leg-B + leg-C.** Blocks all Phase 4 — nothing dispatches without `resolve()`. |
| **S10** | **K9** (peer) | **06** (draft pipeline) + **09** (due-queue + version policy leg) | **06:** producer-agnostic `sb_drafts`, N-ops-as-N-rows, Accept=AND-over-refs, per-op idempotent-resume over K7 `run()`. **09:** `sb_due_queue` + `ManagedTaskSpec` durability/misfire/catch-up, `arm_declared_tasks`, boot-reconcile, `VersionPolicy`/`VersionedRow`. **Register `ExpiryJanitorLane` + `DueQueueLane` (+ 11's `InvariantSweepLane`) on 09's `PollSupervisor`.** | **K3** (`once`/txn) + **K6** (`resolve_authority`) + **K7** (`run()`/`run_ref`) + **K8** (envelope) + **K2** (ref table) + **K1** (op-kind/task-key reservation) | **F-2** (draft ops ride K7 `run()` per-op). GLOBAL slot-key double-arm **closed** via `COALESCE(guild_id,0)` (09 §5). 06 & 09 are **peers on the K3 substrate** (no dependency between them). Blocks AI orchestration, presets, restart-safe timers, all `DURABLE` tasks, `bears_value` cross-deploy state. |
| **S11** | rides frozen grammar (Gate-0 leaves + K7) | **10** (security / abuse rubric) | rubric classes 11/12/13 (rubric v2); `CommandSpec.cost_posture`+`quota_ref`+`check_cost_posture`; `StoreSpec.{data_class,erasure_ref,cache_scope}`+`check_data_lifecycle`; member-erasure executor `sb/kernel/privacy/erasure.py`; **new `ChannelEmitter` egress port** (`kernel/interaction/egress.py`) + AST send-fence | **K7** (`erasure_ref`→`run_ref`→`emit_audit_action`); frozen `SurfaceResponder` (02); metrics (05) | **RC-21** (`ChannelEmitter` send-egress port — a pending 02/K8 seam correction, `UNTRUSTED`⇒`AllowedMentions.none()`, homed Q-D26). Strand-3. Adversarial-abuse pass = a Gate-0 checklist line (owner-gated Q-D20). |
| **S12** | rides K5/K9 + K7 | **11** (data-integrity / repair) | `sb/spec/invariants.py` (`InvariantSpec`, §2.8 sibling of `StoreSpec`) + `data_invariants` facet; `invariant_coverage` fence; `InvariantSweepLane` (a `PollLane` on **09's** `PollSupervisor`, peer to due-queue + draft janitor); `sb_quarantine` + `sb_invariant_sweep_log`; CUT-2 verify-import; `QUARANTINE_ONLY` money-repair default | **K7** `run_ref(conn=)` external-conn + vocab ④ `once()` (the 09 `_fire_one` pattern verbatim); **09** `PollSupervisor`; K3 | **F-4/RC-18** (`SWEEP_ACTOR.actor_type="backfill"`), **RC-19** (sweep-repair exc → `from_exception(…, MAINTENANCE, None)`). Strand-3. Report-only default; auto-repair is a settings-backed one-way door. Money-repair direction owner-gated (Q-D13). |
| **S13** | Gate-0 leaf + K9 | **12** (credential lifecycle) | `sb/spec/credentials.py` (`CredentialSpec`, `RotationPosture`/`RevocationRef`/`BlastTier`) + `CREDENTIAL_REGISTRY` + `check_credential_lifecycle.py`; rotation as a **`DURABLE` `OneShot` `ManagedTaskSpec` on 09's due-queue** + `phase` ledger; `requirements.lock` + `check_lockfile_fresh` + `pip-audit` gate; compromise runbook | **09** due-queue (`ManagedTaskSpec` + `reconcile_on_boot` re-fires crash-interrupted swap); **05** `SecretSpec` | Sibling-leaf discipline (does **not** mutate `SecretSpec`/§6.1; `config_ref` names the `SecretSpec.env_var`). Strand-3. Custody/recovery calls owner-gated (Q-D16/17/19); revocation carve-out narrows binding Q-0213 → router DISCUSS. |
| **S14** | Gate-0 grammar (on 09's `StoreSpec`) | **13** (backup / DR / rollback) | de-repo-bound backup port + verified-restore CI job (`restore-verify.yml`) + `SB_VERIFY_BOOT` ConfigSpec (the 48th field); RPO contract; `RollbackClass` enum + **derived `rollback_class`** on **09's** version-extended `StoreSpec`; `rollback_class_resolved` + reverse-importer fence; narrow reverse importer | **09** `sb/spec/versioning.py` `StoreSpec`; the **01** manifest compiler (for the derivation); **11** §2.5 sweep (for verified-restore) | Additive-not-fork: `SB_VERIFY_BOOT` moves the config count 47→48. Strand-3. Rollback-data disposition + window N = the near-irreversible owner-only call (Q-D15); RPO target owner-gated (Q-D14). |
| **S15** | seam-correction into K0 + CUT stages | **14** (platform-governance) | slash-first survivability tag + `check_intent_survival`/`check_slash_cap`; **`IntentPosture` DEGRADE seam-correction into 05's `IntentSpec`** (**OPEN-FORK F-3 → PG-2**); `guild_count` gauge + ~75/90 latched threshold evaluator; `tools/permission_census.py` (CUT-2 gate) + rename-override carry-verify + admin-notice | **05** `IntentSpec`/`assert_intents` (K0); the CUT-2 importer | **F-3 is the ONE open contested seam** — `05` keeps `required=True` fail-closed; `14` proposes `required=False`+`DEGRADE`. **Carried to owner register PG-2, NOT closed by edit.** Strand-3. App-id + verification-milestone calls owner-gated (PG-1/PG-3/PG-5). |

---

## 3. The six explicit callouts

- **(a) 01 is the compiler linchpin, built first** among the real kernel bands. It lands at **K2** and is
  "the gate the entire kernel and port order sit behind" (01 §11). Its only earlier dependency is **K1
  (03)**, because 01's P3 namespace pass *is* a call into K1's `validate` (**RC-7**). Its
  amendment-registry half (§3.7) is the **pre-Gate-0 prerequisite (S0)**.
- **(b) 05's `IdempotencyKey`/`once()`/`db.transaction()` (K3) + 04's authority contracts (K6) are the
  strand-2 substrate.** All of 06/07/08/09 consume the K3 idempotency+transaction primitive; every K7
  workflow lane calls 04's `resolve_authority` as its first step. Strand-2 cannot build until both land
  (**S4 + S7**).
- **(c) The spec-02 absorption edit is an explicit L0 task (S9).** 02 is written to its pre-hardening
  shapes and must absorb 04's frozen authority contracts **RC-2/3/4/5/13/14/15 + `actor_type`** before K8
  wires up. Status: **F-4/RC-18 (`actor_type`) has landed** on 02's `ActorRef`; **RC-12 (`member_tier`)
  is still pending** in this batch, along with threading `owner_override` into channel-access and naming
  the `TransparencySink` seam.
- **(d) 07 (K7) underlies 06 + 09; 08 provides durable delivery.** 07 is the strand-2 keystone — 06's
  `apply_draft` calls K7 `run()` **per-op**, 09's `_fire` calls K7 `run_ref()`, and the
  game/scheduler/invariant paths all route through `CompoundOpSpec`s. **08 (K4)** supplies the durable
  `event_outbox` + `enqueue_audit_action` twin that K7 and every `AT_LEAST_ONCE` path emit through.
- **(e) The applied seam reconciliations are already in-spec (not open work):**
  - **F-1 / RC-20** — **09 hosts the outbox relay/reaper lanes** on its single `PollSupervisor` at 5 s;
    the standalone 1 s `RELAY_TASK` model is withdrawn; 08 already host-cites 09. *(landed S5 authored /
    S6 registered)*
  - **F-2 (PIN-2)** — the **draft `run()` caller-type split**: EFFECT-bearing draft ops → `run(spec,ctx)`
    per-op (per-op-atomic + idempotent-resume); `run_ref`/`apply` = external-conn pure-DB only, fenced by
    a **narrowed `atomic_db_only`** (no draft `op_kind` in scope → the 10-channel D&D canary un-blocks).
    Applied in both 06 and 07. *(landed S8/S10)*
  - The two former **blockers are closed**: the **GLOBAL slot-key double-arm** (09 `COALESCE(guild_id,0)`
    in the unique index; arm-key ≡ fire-dedup-key normalization) and the **`atomic_db_only` fence scope**.
    A green build is no longer structurally blocked.
- **(f) Strand-3 (10–14) rides the frozen grammar.** It adds **no** new kernel ordering: it consumes the
  frozen vocab, K7 `run_ref`, 09's `PollSupervisor`, and the Gate-0 grammar leaves; specs 10–14 can build
  in parallel once K7/K9 exist and the grammar is frozen. Each adopts the §4 owner rulings.

---

## 4. Where each of the 14 specs lands (spec → step map)

| Spec | K-slot(s) | Step(s) | Note |
|---|---|---|---|
| **01** compiler/snapshot/amendments | **pre-Gate-0 + K2** | **S0, S3** | amendment registry (S0) precedes the Gate-0 fold; compiler (S3) is the linchpin. |
| **02** resolver + error envelope | **K6 (leaf) + K8 (resolver)** | **S7, S9** | leaf/resolver split breaks the 02↔07 cycle; the S9 absorption edit is an explicit L0 task. |
| **03** namespace registry | **K1** | **S2** | leaf; only K0 upstream. |
| **04** authority engine | **K6** | **S7** | strand-2's authority substrate. |
| **05** config + db + health | **K0 + K3 + K5** | **S1, S4, S6** | the floor; three landing points (config / db seam / health). |
| **06** draft pipeline | **K9** | **S10** | peer of 09 on the K3 substrate. |
| **07** workflow engine | **K7** | **S8** | strand-2 keystone; underlies 06 + 09. |
| **08** event outbox | **K4 (authored) + K5 (registered)** | **S5, S6** | relay/reaper authored at K4, registered on 09's supervisor at/after K5. |
| **09** scheduler state | **K5 (poll host) + K9 (due-queue)** | **S6, S10** | two landing points. |
| **10** security/abuse rubric | rides frozen grammar + K7 | **S11** | strand-3. |
| **11** data-integrity/repair | rides K5/K9 + K7 | **S12** | strand-3; `InvariantSweepLane` on 09's supervisor. |
| **12** credential lifecycle | Gate-0 leaf + K9 | **S13** | strand-3; rotation on 09's due-queue. |
| **13** backup/DR/rollback | Gate-0 grammar on 09's `StoreSpec` | **S14** | strand-3; consumes 01 for the `rollback_class` derivation. |
| **14** platform-governance | seam-correction into K0 + CUT | **S15** | strand-3; carries the one open fork F-3. |

**Multi-slot spans (span >1 K-slot):** **01** (S0+S3), **05** (S1+S4+S6), **09** (S6+S10), **02**
(S7+S9), and **08** (S5 authored / S6 registered).

---

## 5. Broken apparent cycles + the strand-3 rider

- **No true circular dependency exists.** Two *apparent* cycles are structurally broken:
  1. **02 ↔ 07** — 02's pure `outcomes.py` leaf (`from_exception`/`Result`, landed at **K6** per 04's
     recommendation) is consumed by 07 at K7, while 02's *resolver* lands later at **K8** and consumes
     07. Splitting the leaf from the resolver removes the cycle.
  2. **08 ↔ 09** — 08 is authored at **K4** but its relay/reaper lanes are only *registered*
     (composition-root) at/after **K5** on 09's `PollSupervisor`; 08's enqueue/store depend on K3, not on
     09. The authored-early / registered-later pattern removes the cycle.
- **Strand-3 rides the frozen grammar** — 10–14 add no kernel ordering and build in parallel on the K7 +
  K9 + frozen-vocab substrate once the grammar is frozen.
- **One reconciliation still pending in-batch (not contested, just not yet applied):** **RC-12
  (`member_tier` on 02's `ActorRef`)** — part of the S9 absorption edit; must land before K8.
- **The "arms-later" contracts are not ordering violations:** 01's P7 (arms at K3), leg-B/leg-C (arm at
  K8), 03's `validate` end-to-end run (arms at K2), and 04's P4 arming (at K6) are contracts *defined* at
  their own slot that *activate* when a downstream input lands — deliberate, per the sibling-01 pattern.

---

## 6. The one OPEN contested edge — F-3 (carried, not closed)

**F-3 (`14 §2.B` ↔ `05 §3.1`) — intent-denial posture.** `05` declares `message_content`/`members`
**`required=True` ⇒ `FAILED_STARTUP`** on denial (fail-closed, the safe default). `14` proposes flipping
both to **`required=False` + `IntentPosture.DEGRADE`** (boot slash-only with a `DegradedCapability`
notice) + the enforced mirror invariant `required == (posture is REQUIRED)`, routing it as a **seam
correction to `05`**.

**Status: owner-gated — carried to owner register PG-2, NOT resolved by edit.** `05` keeps fail-closed
as the built default that ships until the owner rules; `14`'s DEGRADE flip stays a proposed correction.
`05 §3.1` gains `IntentPosture`/`degrades` + the mirror invariant **only once PG-2 is approved.** No spec
edit closes this in the current pass. It is the **single** cross-spec fork still open; F-1/F-2/F-4/F-5 are
all RESOLVED-and-applied.

---

## 7. Verification note — the one §11 disagreement, and who won

**Edge: placement of 02's `outcomes.py` leaf (`from_exception`/`Result`/`ErrorClass`/`DenialReason`/
`ReplyVisibility`/`DeferMode`).**

- **Spec `02 §11`** places the leaf at **K7** ("K7 … land `sb/spec/outcomes.py` … `Result` … the
  `WorkflowResult → §2.7` pass-through … and `from_exception` — they are pure, spec-leaf").
- **Spec `04 §11`** *recommends* landing the leaf one band earlier at **K6** ("Uses
  `DenialReason`/outcome constants from `sb/spec/outcomes.py` … the *leaf* can precede — recommend
  landing `outcomes.py` at K6 so authority need not forward-reference K7").

**Resolution: 04's K6 recommendation wins in this plan** (S7 lands the leaf, S8 finalizes the
`WorkflowResult`/`from_exception` grammar). Rationale: both specs agree the leaf is **pure** and may
precede its consumer; K6 is the earlier, cycle-breaking placement that lets the K6 authority engine
consume `DenialReason`/outcome constants without forward-referencing K7. This is a **placement
refinement, not a contradiction** — the leaf is authored at K6 and its workflow-facing grammar
(`WorkflowResult`) is finalized at K7 alongside 07. It does not change any dependency edge or the build's
correctness. Every other §11 K-slot placement and dependency edge verified **AGREES** with the work-list.

---

*Consolidated 2026-07-04 over Part 3 of the Gate-0 work-list, verified against the 14 specs' §11
build-order sections and the applied reconciliations in the seam-consistency matrix (F-1/F-2/F-4/F-5
RESOLVED; F-3 OPEN → PG-2). **NOT SOURCE OF TRUTH** — the plan the later, separate new-repo Phase-B L0
build executes; the 14 specs win for any shape they own (Q-0120).*
