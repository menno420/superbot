# Strand 2 · Runtime durability · ④ The C-2 draft / preview / confirm / apply pipeline (producer-agnostic)

> **Phase-B design spec. Buildable-depth. DOCS-ONLY — authors no `disbot/` and no `sb/` code.**
> Design INTO the frozen design-spec (`docs/planning/rebuild-design-spec-2026-07-02.md`) §2.6
> (PanelActionSpec), §2.7 (WorkflowResult / MutationPreview / ConfirmationSpec), §4.5 (legacy-KV
> route-truth) and the conventions freeze
> (`docs/planning/rebuild-conventions-invocation-authority-2026-07-03.md`) §2.4 (goal→draft→preview→
> Accept→execute), §4 (authority), §6 (C-2 centralization). Design AGAINST frozen router answers
> Q-0219…Q-0237 (incl. Q-0237a-g) — never re-decide them.
>
> **Consumes the FROZEN shared vocabulary**
> (`../shared-vocabulary.md`): the error envelope ①, `authority_ref`/`resolve_authority` ②, the
> audit-row semantics ③, the idempotency-key contract ④, the restart-safety pattern ⑤. Where the vocab
> left a skeleton for me to COMPLETE — the per-action `dedup_token` for draft-apply (④.2), the
> one-row-vs-N compound-apply correlation (③.3) — I complete it here consistently with the skeleton.
>
> **Sibling reconciliation (this revision, 2026-07-04).** The three other strand-2 specs are now
> WRITTEN and this spec is reconciled against their SHIPPED shapes (source-wins, Q-0120):
> - **K7 workflow engine (`07-workflow-engine.md`)** exposes `run(spec: CompoundOpSpec, ctx) ->
>   WorkflowResult` and `preview(spec: CompoundOpSpec, ctx) -> MutationPreview` (07 §3.2) — **per
>   `CompoundOpSpec`, each opening its OWN `db.transaction()` (07 §3.3 step 4) and emitting ONE central
>   audit row (07 §3.4)**. There is **no `engine.apply(op)`** and **no per-`DraftOperation` entry**. This
>   spec's earlier assumption of `engine.apply(op, *, conn)` / `preview(op, ctx)` was wrong; every call
>   site is rewritten to resolve each `DraftOperation` → a `CompoundOpSpec` (via the op-kind registry
>   §3.3) → `engine.run(spec, ctx)` / `engine.preview(spec, ctx)`. **07 *does* also declare external-conn
>   PURE-DB entries `run_ref(ref, ctx, *, conn)` / `apply(…)`, but they are `atomic_db_only`-fenced and
>   reserved for the scheduler/invariant pure-DB callers — NOT a per-`DraftOperation` entry; this pipeline's
>   EFFECT-bearing draft ops stay on `run(spec, ctx)` per-op (F-2 resolved by caller type, §12).** K7 owns
>   the per-op DB/EFFECT split,
>   the per-op `once()` idempotency, and the per-op audit row; **this pipeline orchestrates the ordered
>   sequence and the correlation id**, nothing lower.
> - **audit_log carries a nullable `correlation_id uuid` COLUMN** — already added by 07 §5 and
>   08-event-outbox §5.1. The correlation seam is therefore **resolved by column** (§12), not the stale
>   "add a 12th `emit_audit_action` field OR encode into `target`" fork this spec used to present. The
>   one remaining mechanical gap is a `correlation_id` FIELD on K7's `WorkflowContext` to POPULATE the
>   column — a seam-correction flagged for 07 (§12), consistent with 07 §8 fork B already assigning ④
>   the N-invocation loop + id.
> - **09-scheduler-state** owns the `ExpiryJanitorLane` that runs this pipeline's `select_expired` sweep
>   (09 §3.7/§4). The earlier "OR lazily at `load_draft`" alternative is deleted (a read primitive must
>   not mutate — §6).
>
> **Source-wins (Q-0120).** Spot-verified this session against shipped source: the draft store is a
> per-guild **singleton** (`utils/db/setup_draft.py`, unique index on the slot key — no `draft_id`/
> `producer` column); the Accept gate is hard-wired to setup-admin (`views/setup/final_review.py:60-94`
> `_gate_apply` → `setup_access.can_apply_setup`); apply is **non-atomic** (`:659-701`
> `_apply_ops_in_order` → per-op single-op batches through `services.setup_operations.apply_operations`,
> `:803-838`, no surrounding transaction); the read-only diff `preflight_operations`
> (`services/setup_operations.py:362`) + `setup_change_plan.ChangePlanEntry` (`:174`) has **ZERO
> view/cog consumers** (grep-verified — the docstring's "PR-04b default-on, Final Review calls it"
> wiring was never landed). There is **no `class WorkflowResult`** and **no `disbot/core/contracts.py`**
> (both re-confirmed ABSENT) — the real seams are `disbot/services/lifecycle/contracts.py`
> (`LifecycleResult` :77, `LifecyclePreview` :66, `StepResult` :56, outcomes :48-52, reversibility
> :40-42) and `emit_audit_action` (`services/audit_events.py:52`, 11 keyword-only fields). The shipped
> dispatch-result analogue is `StageResult` (`core/runtime/message_pipeline.py:181`) — **not** a
> dispatch return and not used here.
>
> **Anti-pad (Q-0089).** The design spec ALREADY fixes the single-op shapes: §2.7 designs
> `MutationPreview` (superset of `LifecyclePreview`) and `ConfirmationSpec`
> (`challenge/timeout_s/re_check_actor/snapshot_before`); §2.6 gives `PanelActionSpec.confirm`; §2.4
> narrates goal→draft→preview→Accept→execute; C-2 (§6) names "one pipe, two producers." This spec does
> **not** restate those. It shapes the six genuinely-undesigned contracts underneath them: the
> **multi-op durable draft primitive** keyed `(producer, owner_scope, draft_id)`, the **fail-closed
> op-kind registry**, the **Accept-authority derivation** for non-setup producers, the **batch
> aggregation** of §2.7's single-op preview/confirm, the **sequenced/idempotent apply** semantics over
> K7 for non-rollback-able Discord ops, and the **test-mode / `verified_live` plug-point**.

---

## 1. Summary + the exact undesigned gap

Conventions §2.4 calls C-2 *"not new architecture — the already-designed draft lane with a new
producer."* **That premise is false in shipped source** (FJ L-7, re-verified). The shipped draft lane
cannot carry a second producer and cannot represent the flagship example:

| Surface | Shipped state (verified this session) | Cite |
|---|---|---|
| Draft store | **Per-guild SINGLETON.** Unique index `(guild_id, op_kind, subsystem, COALESCE(setting_name,''), COALESCE(binding_name,''))`; `insert` upserts on that slot; `clear(guild_id)` wipes the whole guild. No `draft_id`, no `producer` column. | `utils/db/setup_draft.py:10-33,88-247,357-375` |
| 10-channel draft | **Unrepresentable.** 10 `create_channel` ops for one subsystem share the slot key (`resource_name` is **not** in the key) → they collapse to **1 row**. Two producers writing the same guild destructively merge. | slot-key def `:184-188` |
| Accept gate | **Hard-wired to setup authority.** `can_apply_setup(member, session)` — server owner or delegated setup admin only. No derivation for AI/preset/NL producers. | `views/setup/final_review.py:86-93` |
| Apply | **Non-atomic.** Each op applied as its own single-op batch in phase order; per-op isolation; partial-apply is a first-class terminal state (`PartialApplyRecoveryView`). No transaction, no idempotency key. | `views/setup/final_review.py:659-701`; `services/setup_operations.py:830-838` |
| Preview | A real current/proposed **diff exists** (`ChangePlanEntry{current, proposed, would_change, risk}`) but has **ZERO consumers** — env-gated dead code. | `services/setup_change_plan.py:174-221`; grep |

**The gap this spec closes (nothing else designs it):** the producer-agnostic batch draft *primitive*
keyed `(producer, owner_scope, draft_id)` that makes the 10-channel draft representable and lets two
producers coexist; the **fail-closed** op-kind registry (a kind with no adapter is *un-draftable*, not
cosmetically "preflight unavailable"); the Accept-authority *derivation* so non-setup producers gate
correctly (and the bot-owner can Accept in a friend's server, Q-0227); the **batch** aggregation of
§2.7's single-op `MutationPreview`/`ConfirmationSpec`; the **sequenced-per-op-atomic / idempotent apply**
over the K7 engine; and the **`verified_live` plug-point** (release-testing-loop D). `preflight_operations`
is **retired into** the workflow engine's `preview()` (§8 fork 5).

---

## 2. Files / modules it becomes

**New `sb/` paths** (kernel layer — imports `sb/spec/*`, `sb/kernel/db/*`, `sb/kernel/authority/*` K6,
the K7 workflow-engine port, the K2 ref table; **never** views/cogs):

| Path | Owns |
|---|---|
| `sb/spec/draft.py` | leaf: `Producer`, `DraftStatus`, `ConfirmChallenge` enums; `DraftOperation`, `Draft`, `OwnerScope`, `VerificationContext`, `ConfirmationResponse` dataclasses; the `AcceptHook` port protocol |
| `sb/kernel/db/draft.py` | DB primitive (asyncpg only): `sb_drafts` + `sb_draft_operations` CRUD; append-by-`op_seq` (**no** slot upsert) |
| `sb/kernel/draft/store.py` | domain store over the db primitive: `create/add/remove/load/list_open/discard/select_expired` |
| `sb/kernel/draft/registry.py` | `OpKindRegistry` (fail-closed op-kind slot) + `OpKindBinding` — the ONE key `op_kind → (WorkflowRef, payload_schema, is_resource_create)` |
| `sb/kernel/draft/preview.py` | `build_draft_preview`, `DraftPreview`/`PreviewBlock`/`DraftConfirmationSpec` batch shapes, `PreviewContext`, `requires_confirmation`, `verify_confirmation` |
| `sb/kernel/draft/accept.py` | `derive_accept_authority`, `resolve_draft_accept` (AND-over-distinct-refs for mixed drafts) |
| `sb/kernel/draft/apply.py` | `apply_draft`, `DraftApplyResult`; the sequenced/idempotent orchestrator over the K7 engine |
| `sb/kernel/draft/pipeline.py` | `DraftPipeline` facade (create→add→preview→confirm_and_apply→discard) + the draft-lane error types |

**Retired shipped paths** (§10 maps each to an L-row):

| Retired | Replaced by |
|---|---|
| `disbot/utils/db/setup_draft.py` (singleton store) | `sb/kernel/db/draft.py` (keyed `draft_id`, ops keyed `(draft_id, op_seq)`) |
| `disbot/services/setup_draft.py` (service wrapper, staging-kind rules) | `sb/kernel/draft/store.py` |
| `disbot/services/setup_operations.py::preflight_operations` / `preview_operations` / `is_preflight_enabled` / `preflight_gate_state` | K7 `WorkflowEngine.preview(spec, ctx)` behind the op-kind registry |
| `disbot/services/setup_change_plan.py` (`ChangePlanEntry` dead diff) | `MutationPreview.diff: tuple[FieldChange,...]` (§2.7); the current/proposed read logic **ports into** the workflow engine's per-lane `preview()` |
| `disbot/views/setup/final_review.py::_gate_apply` | `sb/kernel/draft/accept.py::resolve_draft_accept` (derived, not hard-wired) |
| `disbot/views/setup/final_review.py::_apply_ops_in_order` + `apply_operations` (as the *apply seam*) | `sb/kernel/draft/apply.py::apply_draft` (per-op dispatch logic ports into each op-kind's K7 `CompoundOpSpec`) |

Final Review, the rung-4 AI-orchestration cog, C-3 preset instantiation, and the release-test flow all
become **thin Discord surfaces** over `DraftPipeline` — none re-implements staging, preview, gate, or apply.

---

## 3. The complete public contract

Tags: **[S]** manifest/spec field · **[O]** objective input · fields with no tag are **durable runtime
state** (DB rows) or derived values, explicitly not manifest fields.

### 3.1 `sb/spec/draft.py` — the leaf

```python
class Producer(StrEnum):                    # the (producer, …) key component — WHO composed the draft
    HUMAN_SETUP       = "human_setup"       # setup wizard click-through
    AI_ORCHESTRATION  = "ai_orchestration"  # rung-4 NL goal→draft (§2.4)
    PRESET            = "preset"             # C-3 template instantiation
    FUZZY_DESTRUCTIVE = "fuzzy_destructive"  # a typo-corrected destructive action (rung-2)
    NL_ACTION         = "nl_action"          # rung-3 NL intent → single action
    RELEASE_TEST      = "release_test"       # test-mode verified_live sign-off (release-testing-loop D)
    IMPORT_REPAIR     = "import_repair"      # operator repair / recovery draft

_AI_PRODUCERS = frozenset({Producer.AI_ORCHESTRATION, Producer.NL_ACTION, Producer.FUZZY_DESTRUCTIVE})

class DraftStatus(StrEnum):
    OPEN      = "open"       # accepting ops / edits
    PREVIEWED = "previewed"  # preview built, awaiting confirm (preview_hash pinned)
    APPLYING  = "applying"   # apply in progress — crash-visible (restart reconcile reads this)
    APPLIED   = "applied"    # terminal: full success
    PARTIAL   = "partial"    # terminal: ≥1 op failed; recovery re-run available (already-applied ops skip)
    DISCARDED = "discarded"  # terminal: operator dropped it
    EXPIRED   = "expired"    # terminal: TTL elapsed unapplied (written ONLY by 09's ExpiryJanitorLane)

class ConfirmChallenge(StrEnum):            # §2.7 verbatim
    BUTTON = "button"; TYPED_PHRASE = "typed_phrase"; TYPED_HASH = "typed_hash"

@dataclass(frozen=True)
class OwnerScope:                           # the (…, owner_scope, …) key component — WHO is accountable
    guild_id: int                           # the TARGET guild (write target)
    actor_id: int | None                    # accountable producer identity; None for system/backfill
    def render(self) -> str: ...            # f"g{guild_id}:a{actor_id or 0}" — DISPLAY/log key ONLY,
                                            #   NEVER the SQL predicate value (owner_actor_id is NULL for
                                            #   system rows; list_open_drafts uses IS NOT DISTINCT FROM, §3.2)

@dataclass(frozen=True)
class DraftOperation:
    op_seq: int                             # 1-based order WITHIN the draft — the 10-channel fix (identity ≠ slot)
    op_kind: str            # [S]           # the ONE registry key (bind_channel, create_channel, set_setting, …);
                                            #   MUST resolve in the OpKindRegistry (§3.3) or the op is un-draftable
    subsystem: str          # [S]
    authority_ref: str      # [S]           # the op's own §2.4 authority label — fed into accept-authority (§3.4)
    payload: Mapping[str, Any]              # typed per op_kind against the binding's payload_schema (§3.3);
                                            #   flows to K7 as WorkflowContext.params at apply/preview time
    label: str                              # human one-liner rendered in preview
    dedup_token: str                        # apply-idempotency natural key; default f"{draft_id}:{op_seq}".
                                            #   Passed to K7 as ctx.params["_draft_dedup_token"] — the draft owns the
                                            #   TOKEN VALUE (completes ④.2); K7's per-op once() owns the GUARD (§3.5).
    # NOTE: is_resource_create and the preview provider are NOT op fields — both are DECLARED registry
    #       properties on the OpKindBinding (§3.3), resolved by op_kind. (Retires the old per-op
    #       preview_provider field and the create_*-prefix derivation — critic findings #6/#8/#10.)

@dataclass(frozen=True)
class VerificationContext:                  # the test-mode / verified_live plug-point payload
    test_mode: bool                         # True ⇒ apply threads test_mode into every op's WorkflowContext (§3.5);
                                            #   built default = K7 EFFECT legs suppress real Discord writes (§9 def. 6)
    debug_channel_id: int | None            # where the full debug trace / suppressed-effect plan renders (loop C)
    sign_off_store_ref: str | None          # where the verified_live sign-off is recorded (D / Q-0234 / Q-0222)

@dataclass(frozen=True)
class ConfirmationResponse:                 # the challenge-satisfaction input to confirm_and_apply (§3.6)
    challenge: ConfirmChallenge             # which challenge the user answered
    typed_value: str | None                 # None for BUTTON; the user's typed string for TYPED_PHRASE/TYPED_HASH

@dataclass(frozen=True)
class Draft:
    draft_id: str                           # uuid4 — the PK, the primitive's identity
    producer: Producer
    owner_scope: OwnerScope
    status: DraftStatus
    operations: tuple[DraftOperation, ...]  # ORDERED by op_seq; N rows coexist (10 create_channel = 10 rows)
    created_at: datetime
    updated_at: datetime                    # bumped on every add/remove — invalidates a stale preview_hash
    expires_at: datetime | None
    accept_authority_ref: str               # DERIVED display/list floor (§3.4); the ACTUAL gate is the
                                            #   per-distinct-ref AND check in resolve_draft_accept (§3.4)
    correlation_id: str                     # = draft_id — the shared audit correlation id (§3.5 / ③.3 / §12)
    verification: VerificationContext | None

class AcceptHook(Protocol):                 # port — the concrete impl lives in the release-testing band
    async def on_confirmed(self, draft: Draft, decision: "AuthorityDecision") -> None: ...
        # fires in confirm_and_apply AFTER authority+challenge pass, BEFORE the first op runs (§3.6)
    async def on_applied(self, draft: Draft, result: "DraftApplyResult") -> None: ...
        # fires after apply_draft returns any terminal outcome (§3.5 step 6)
```

### 3.2 `sb/kernel/db/draft.py` — DB primitive (asyncpg only, no other imports)

```python
async def insert_draft(draft: Draft, *, conn) -> None
async def append_operation(draft_id: str, op: DraftOperation, *, conn) -> int   # op_seq = COALESCE(MAX,0)+1 — APPEND, never upsert
async def delete_operation(draft_id: str, op_seq: int, *, conn) -> int          # returns rowcount
async def load_draft(draft_id: str, *, conn) -> Draft | None                    # READ-ONLY; joins ops, ordered by op_seq — NEVER mutates status
async def list_open_drafts(scope: OwnerScope, *, conn) -> tuple[Draft, ...]     # see NULL-safe predicate below
async def update_status(draft_id: str, status: DraftStatus, *, conn,
                        expect: DraftStatus | None = None) -> bool              # bumps updated_at. When `expect` is given this is a
                                                                               #   CONDITIONAL compare-and-set (UPDATE … WHERE status=expect),
                                                                               #   returning whether the row transitioned (rowcount == 1);
                                                                               #   expect=None keeps the old unconditional overwrite.
async def reap_stuck_applying(now: datetime, ttl_s: int, *, conn) -> tuple[str, ...]  # CONDITIONAL CAS sweep, ONE statement:
                                                                               #   UPDATE sb_drafts SET status='partial', updated_at=now()
                                                                               #   WHERE status='applying' AND updated_at < now() - ttl_s
                                                                               #   RETURNING draft_id. 09's stuck-APPLYING lane calls this (§6);
                                                                               #   the TTL predicate means a legitimately slow apply is NEVER reaped.
async def delete_draft(draft_id: str, *, conn) -> int                          # hard-delete on discard
async def select_expired(now: datetime, *, conn) -> tuple[str, ...]            # READ: draft_ids past expires_at, non-terminal
```

- **`list_open_drafts` is NULL-safe on `owner_actor_id` (critic finding #15).** `OwnerScope.render()`'s
  `a{actor_id or 0}` is a display/log key; the DB column stores **NULL** for system/backfill actors, so
  the query keys on `WHERE owner_guild_id = $1 AND owner_actor_id IS NOT DISTINCT FROM $2 AND status IN
  (OPEN, PREVIEWED, APPLYING)`. `IS NOT DISTINCT FROM` matches NULL=NULL and value=value uniformly — a
  bare `= $2` would silently miss the system rows.
- **`load_draft` and `select_expired` are READ-ONLY** — neither writes `EXPIRED`. The `OPEN/PREVIEWED →
  EXPIRED` transition is a WRITE owned by **09's `ExpiryJanitorLane`** (which calls `select_expired` →
  `update_status(EXPIRED)` under its poll, 09 §3.7/§4), never lazily at load time (§6).
- **`reap_stuck_applying` is a strictly-CONDITIONAL compare-and-set** (`WHERE status='applying' AND
  updated_at < now() - ttl_s`) — it can only ever move a **stale** `APPLYING` row to `PARTIAL`. A live apply
  that is merely slow (a large multi-channel draft) keeps its `updated_at` fresh via the per-op heartbeat
  (§3.5 step 2) and is invisible to the reaper until it genuinely stops progressing for the whole TTL. 09's
  stuck-`APPLYING` lane owns the *cadence* (a registered `PollLane`); this primitive owns the *atomicity*, so
  the reaper and a completing `apply_draft` can never clobber each other (the matching conditional write is
  `update_status(APPLIED, expect=APPLYING)`, §3.5 step 5).

### 3.3 `sb/kernel/draft/registry.py` + `preview.py` — fail-closed op-kind slot + batch shapes

The **op-kind registry** is the single fail-closed slot. It is keyed by `op_kind` (the ONLY key —
retiring the ambiguous per-op `preview_provider` field, critic finding #8) and each binding declares
everything the pipeline needs to preview, apply, and gate an op of that kind:

```python
# sb/kernel/draft/registry.py
@dataclass(frozen=True)
class OpKindBinding:
    op_kind: str
    workflow_ref: "WorkflowRef"             # [S] resolves (K2 ref table) → the STATIC CompoundOpSpec that K7
                                            #     run()s / preview()s for this op_kind (per-op payload rides ctx.params)
    payload_schema: tuple["FieldSpec", ...] # [S] the fields DraftOperation.payload MUST carry for this op_kind
    is_resource_create: bool                # [S] DECLARED — True ⇒ the op's CompoundOpSpec has a non-rollback-able
                                            #     Discord EFFECT leg (drives the preview warning + the T2-1 aggregate
                                            #     note ONLY; NOT an apply-time control-flow partition — §3.5)

class OpKindRegistry:
    def register(self, binding: OpKindBinding) -> None
    def get(self, op_kind: str) -> OpKindBinding | None    # None ⇒ FAIL-CLOSED
    def is_draftable(self, op_kind: str) -> bool           # False ⇒ op cannot enter a draft (UndraftableOperation at add)
```

`build_draft_preview` resolves each op via `registry.get(op.op_kind)`; a `None` binding yields a
`PreviewBlock(reason=NOT_FOUND, detail="no_op_kind_binding")` and forces `allowed=False`. For a bound op
it resolves `binding.workflow_ref` → the `CompoundOpSpec` (K2 ref table) and calls the **canonical
provider — K7's `engine.preview(spec, ctx)`** (07 §3.2/§3.5, the txn-rollback + skip-effects dry-run
oracle). No separate provider registry exists: the preview provider IS the op's K7 engine preview.

```python
# sb/kernel/draft/preview.py
@dataclass(frozen=True)
class PreviewContext:                       # the input build_draft_preview / pipeline.preview() take (critic finding #1)
    actor: "ActorRef"                       # carries member_tier (RC-12) + user_id/is_member for authority
    guild_id: int                           # the TARGET guild
    member_tier: str | None                 # pre-computed tier in the target guild (RC-12)
    clock: "Clock"
    test_mode: bool = False                 # mirrors draft.verification.test_mode when previewing a RELEASE_TEST draft
    # build_draft_preview constructs, per op, a K7 WorkflowContext(
    #     actor, guild_id, request_id=f"preview:{draft_id}", dry_run=True,
    #     params=op.payload, clock, correlation_id=draft_id, test_mode=test_mode)
    # and calls engine.preview(spec, ctx). (correlation_id/test_mode are the two WorkflowContext fields
    # flagged as seam-corrections for K7 — §12.)

@dataclass(frozen=True)
class PreviewBlock:
    op_seq: int
    reason: DenialReason        # NOT_FOUND (un-draftable) | AUTHORITY | USER_ERROR (invalid) | DISPATCH_ERROR
    detail: str

@dataclass(frozen=True)
class DraftConfirmationSpec:                # §2.7 ConfirmationSpec generalized to a draft (batch level)
    reversibility: str                      # aggregate MAX over ops (shipped constants :40-42)
    challenge: ConfirmChallenge             # compile rule: IRREVERSIBLE ⇒ typed_phrase|typed_hash
    timeout_s: int = 60
    re_check_actor: Literal[True] = True    # FROZEN — confirm always re-resolves authority (§2.7)
    expected_phrase: str | None = None      # for TYPED_PHRASE: the canonical phrase the response must equal
    expected_hash: str | None = None        # for TYPED_HASH: sha256 the response must hash to
    # NOTE: no batch-level snapshot_before. Per-op before-images are captured by K7 (LegOutcome.before/after
    #       → the central row's prev_value, 07 §3.4). A whole-draft rollback snapshot has no consumer under
    #       the compensation deferral (§9) — retired from the batch shape (critic finding #11).

@dataclass(frozen=True)
class DraftPreview:                         # the BATCH shape I own (§2.7's MutationPreview is single-op)
    draft_id: str
    preview_hash: str                       # over (draft_id, updated_at, ops) — pins confirm to this exact op set
    allowed: bool                           # AND over per-op MutationPreview.allowed AND no blocks
    op_previews: tuple["MutationPreview", ...]   # one per applied op, op_seq order (each carries diff/warnings/reversibility)
    aggregate_reversibility: str            # MAX: IRREVERSIBLE > COMPENSATABLE > REVERSIBLE
    warnings: tuple[str, ...]               # flattened per-op warnings + draft-level (mixed-lane, resource-create hints)
    requires_confirmation: bool             # T2-5 rule (below) — STRUCTURALLY gated at apply (§3.5 step 1)
    confirmation: DraftConfirmationSpec
    blocking: tuple[PreviewBlock, ...]      # ops that failed preview

async def build_draft_preview(draft: Draft, ctx: PreviewContext, *, registry: OpKindRegistry,
                              engine: "WorkflowEngine", refs, conn) -> DraftPreview: ...

def requires_confirmation(draft: Draft, aggregate_reversibility: str, op_count: int) -> bool:
    # T2-5: destructive + AI-produced + bulk/compound MUST confirm; single reversible direct-lane op is exempt.
    if draft.producer in _AI_PRODUCERS:              return True   # all AI-produced
    if aggregate_reversibility != "REVERSIBLE":      return True   # any destructive/irreversible
    if op_count > 1:                                 return True   # bulk/compound
    return False

def verify_confirmation(spec: DraftConfirmationSpec, resp: ConfirmationResponse | None) -> bool:
    # The KERNEL verifies the challenge (not the panel). fail-closed: a missing/mismatched response ⇒ False.
    if resp is None or resp.challenge != spec.challenge:                 return False
    if spec.challenge is ConfirmChallenge.BUTTON:                        return True         # presence == confirm
    if spec.challenge is ConfirmChallenge.TYPED_PHRASE:                  return resp.typed_value == spec.expected_phrase
    if spec.challenge is ConfirmChallenge.TYPED_HASH:                    return sha256(resp.typed_value or "") == spec.expected_hash
    return False
```

### 3.4 `sb/kernel/draft/accept.py` — derived accept authority (mixed-draft-safe)

The earlier union-**max**-to-one-string collapse silently stripped a capability op's revoke overlay in a
MIXED draft (a revoked `governance.setup.apply` role could Accept a draft that contained a setup op — critic
finding #14). The fix: **the actual gate is an AND over every DISTINCT op `authority_ref`; the derived
single ref is a DISPLAY/list floor only.**

```python
def derive_accept_authority(operations: tuple[DraftOperation, ...]) -> str:
    # DISPLAY/LIST FLOOR ONLY (Draft.accept_authority_ref). Deterministic union-MAX for the badge/list key.
    # tier_floor(ref): TIER lane → the tier's rank; CAPABILITY lane (dotted or "") → "administrator"
    # (§②.2 v1 admin floor). Take max_floor over ops.
    #   - all ops CAPABILITY-lane AND share ONE ref  ⇒ return that ref (the homogeneous common case)
    #   - else                                       ⇒ return the tier token for max_floor
    # This value is NEVER the sole gate — resolve_draft_accept re-checks every distinct ref (below).
    ...

async def resolve_draft_accept(draft: Draft, req: "AuthorityRequest", *,
                               resolve_authority) -> "AuthorityDecision":
    # THE GATE (mixed-draft-safe, fail-closed). Resolve the actor against EVERY DISTINCT op authority_ref:
    #   refs = {op.authority_ref for op in draft.operations}
    #   for ref in refs: d = await resolve_authority(AuthorityRequest(authority_ref=ref, actor…))
    #                    if not d.allowed: return d          # first denial wins → AcceptDenied (K6 denial_message)
    #   return the LAST allowed decision (or a synthesized allow)   # ALL refs allowed
    # owner_override_holds (member-gated) short-circuits ALL refs to allowed (Q-0227 / SF-b) — computed once
    #   by resolve_authority per ref; a member-gated bot-owner passes every ref uniformly.
    # setup_delegate (Q-0098) flows unchanged via req.actor_type per ref.
    # WHY AND, not union-max: a revoke overlay on ANY single ref (e.g. governance.setup.apply disabled for the
    #   actor's role) MUST veto the whole draft — collapsing to a bare tier token would drop that overlay and
    #   let a revoked role Accept a draft merely because another op needed only a lower tier. THREAT closed.
    ...
```

**Threat note.** A capability op's revoke overlay is now never lost in a mix: the draft is Acceptable
iff the actor independently satisfies each op's authority (or holds the member-gated owner override). This
is strictly stronger than any single-string derivation and matches the shipped per-op `can_apply_setup`
intent generalized to N heterogeneous producers.

### 3.5 `sb/kernel/draft/apply.py` — sequenced per-op-atomic / idempotent over K7

```python
@dataclass(frozen=True)
class DraftApplyResult:
    draft_id: str
    outcome: str                            # §2.7 vocab ONLY: SUCCESS|PARTIAL|BLOCKED|DECLINED|DISCORD_FAILED
    op_results: tuple["WorkflowResult", ...]# one K7 WorkflowResult per op RUN (07/§2.7 design type)
    correlation_id: str                     # = draft_id (also on every op's audit_log row via ctx.correlation_id)
    applied: tuple[int, ...]                # op_seqs that reached SUCCESS
    failed: tuple[int, ...]                 # op_seq that returned non-SUCCESS (apply stops there — SF-f)
    skipped: tuple[int, ...]                # ops not attempted (after the stop) or already-applied (once()=False replay)

async def apply_draft(draft: Draft, decision: "AuthorityDecision", preview: DraftPreview,
                      confirmation: ConfirmationResponse | None, *,
                      engine: "WorkflowEngine", refs, registry: OpKindRegistry,
                      clock, hook: AcceptHook | None) -> DraftApplyResult: ...
```

`apply_draft` procedure (fixed order — buildable, zero further decisions):

1. **Re-check accept + confirmation gate (fail-closed).**
   - `decision.allowed` is the confirm-time re-resolve (`re_check_actor=True`, §3.4). Not allowed ⇒
     `outcome=DECLINED`, **no writes**.
   - **If `preview.requires_confirmation` and `not verify_confirmation(preview.confirmation, confirmation)`
     ⇒ `outcome=DECLINED`, no writes** (critic findings #2/#7 — the L-5 "computed the flag but never
     gated it" class, closed structurally). `confirmed := preview.requires_confirmation → True (verified)`;
     for a non-confirming draft `confirmed := True` trivially. This `confirmed` flag is threaded into every
     per-op K7 `WorkflowContext` so K7's own IRREVERSIBLE confirm-assert (07 §3.3 step 2) is satisfied
     without re-prompting.
2. `update_status(APPLYING)` — makes a crash mid-apply reconcilable (§6; the stuck-`APPLYING` sweep is
   09's). **Per-op heartbeat:** the loop bumps the draft row's `updated_at` as each op starts (a lightweight
   `update_status(APPLYING, expect=APPLYING)` — a no-op status write whose only effect is the timestamp), so
   the stuck-`APPLYING` TTL measures **time since the last op progressed**, not wall-clock apply length. A
   legitimately slow multi-channel apply therefore keeps its row *fresh* and is **never reaped mid-flight**
   (§6).
3. **Sequence the ops in `op_seq` order — one K7 `run()` per op (NO whole-op resource partition).** For
   each `op`:
   - `binding = registry.get(op.op_kind)`; resolve `binding.workflow_ref` → the `CompoundOpSpec` (K2 ref table).
   - Build `ctx = WorkflowContext(actor=decision.actor, guild_id=draft.owner_scope.guild_id,
     request_id=f"{draft.draft_id}:{op.op_seq}", confirmed=confirmed, dry_run=False,
     params={**op.payload, "_draft_dedup_token": op.dedup_token},
     correlation_id=draft.draft_id, test_mode=(draft.verification.test_mode if draft.verification else False),
     clock=clock)`.
   - `result = await engine.run(spec, ctx)` — **K7 owns everything below the op boundary**: the DB legs run
     inside K7's own `db.transaction()`; a `DURABLE_ONCE` op is guarded by `once(IdempotencyKey(op_key,
     guild_id, dedup_token=_draft_dedup_token))` so a recovery re-run of the same draft skips already-applied
     ops (completes ④.2); the ONE central audit row is written with `correlation_id = draft_id` (§12); the
     non-rollback-able Discord create is K7's post-commit EFFECT leg (07 §3.3 step 5), not a draft-level lane.
   - Collect `result`. **Stop on the first non-`SUCCESS`** (SF-f default, vocab §⑧): remaining ops go to
     `skipped`; draft → `PARTIAL`.
4. `classify_outcome`-style rollup over `op_results` → draft `outcome`
   (`SUCCESS` all-SUCCESS · `PARTIAL` ≥1 applied then a stop · `BLOCKED`/`DISCORD_FAILED`/`DECLINED`
   propagated from the failing op's `WorkflowResult.outcome` when nothing applied).
5. **`update_status(APPLIED, expect=APPLYING)` on full success — a CONDITIONAL compare-and-set, never a
   blind overwrite.** It flips to `APPLIED` **only if the row is still `APPLYING`** (draft then eligible for
   GC). If the CAS returns `False`, the reaper won a race — it had flipped the row to `PARTIAL` because this
   apply outran the stuck-`APPLYING` TTL (vanishingly rare given the TTL headroom, §6): apply_draft
   **re-reads** the row, honors the `PARTIAL`, and returns that outcome. The fully-applied ops are already
   durable and a recovery re-run is a no-op (every op `once()`-skips), so no `APPLIED`-over-`PARTIAL` clobber
   and no false success can occur. On the ordinary partial path (a mid-draft op failure) the write is
   `update_status(PARTIAL)` and **`PARTIAL` keeps the draft** for a recovery re-run (already-applied ops skip
   via K7's per-op `once()`).
6. `hook.on_applied(draft, result)` if present (fail-open — a missing hook never blocks apply).

**Atomicity contract (honest, per K7's real API — critic seam #2/#3/#6).** K7's `run(spec, ctx)` opens
its **own** `db.transaction()` per op and emits **one** audit row per op (07 §3.3/§3.4). So the draft is
**sequenced + per-op-atomic + idempotent-resume**, NOT one shared transaction across N ops:
- **Per-op DB atomicity** is guaranteed by K7 (each op all-or-nothing within its own txn).
- **Cross-op all-or-nothing is NOT a default guarantee** — a mid-draft failure leaves earlier ops
  committed; the draft goes `PARTIAL` and the recovery re-run resumes idempotently. (The old "one
  `db.transaction()` across all N pure-DB ops" claim was unachievable against K7's per-op entry and is
  retired.) **07 *does* declare an external-conn entry `run_ref(ref, ctx, *, conn)` (and its `apply`
  sibling), but it is fenced `atomic_db_only` and reserved for PURE-DB callers — 09's scheduler
  `ManagedTaskSpec` handlers and the invariant `repair_refs` / version `compensation_refs`.** Draft
  resource-create ops carry a **post-commit Discord EFFECT leg**, which is exactly what `run_ref`'s
  `atomic_db_only` fence excludes, so they are **not eligible** for a shared pure-DB txn and stay on
  `run(spec, ctx)` per-op. Cross-op shared-txn atomicity is therefore a **structural boundary for the draft
  lane** (its ops bear effects), **not a pending K7 co-decision** — the F-2 fork resolves in this pipeline's
  favor by caller type: EFFECT-bearing draft ops → `run(spec, ctx)`; pure-DB scheduler/invariant callers →
  `run_ref`/`apply` (§12).
- **Resource creates are best-effort, NOT exactly-once** (correcting the earlier overclaim, critic
  finding #3). K7 runs the Discord create as a post-commit EFFECT leg; a crash between the external create
  and its outcome record can orphan a channel or re-create on re-run — the DB `once()` guard covers only
  the DB legs, never the external effect. Orphan/duplicate reconciliation rides the compensation deferral
  (§9) and K7's `compensator` seam.

### 3.6 `sb/kernel/draft/pipeline.py` — facade + error types

```python
class DraftPipeline:
    async def create(self, *, producer: Producer, owner_scope: OwnerScope,
                     expires_in_s: int | None = None,
                     verification: VerificationContext | None = None) -> Draft
    async def add(self, draft_id: str, op: DraftOperation) -> Draft          # raises UndraftableOperation (fail-closed)
    async def remove(self, draft_id: str, op_seq: int) -> Draft
    async def preview(self, draft_id: str, ctx: PreviewContext) -> DraftPreview  # sets status PREVIEWED, pins preview_hash
    async def confirm_and_apply(self, draft_id: str, req: "AuthorityRequest", *,
                                preview_hash: str,
                                confirmation: ConfirmationResponse | None = None) -> DraftApplyResult
    async def discard(self, draft_id: str) -> None
```

`confirm_and_apply` fixed order (the confirm→accept→hook→apply seam):

1. `load_draft`; not found / terminal ⇒ `DraftNotFound` / `DraftClosed`.
2. Re-build (or load the pinned) `DraftPreview`; **`preview_hash` ≠ current ⇒ `StalePreview`** (the op set
   changed — re-preview required).
3. `decision = await resolve_draft_accept(draft, req, …)`; denied ⇒ `AcceptDenied` (K6 `denial_message`).
4. **`verify_confirmation(preview.confirmation, confirmation)` when `preview.requires_confirmation`** —
   unmet ⇒ `ConfirmDeclined`. (The same gate apply_draft re-asserts fail-closed at §3.5 step 1; verifying
   here lets the facade reject before touching `APPLYING`.)
5. `await hook.on_confirmed(draft, decision)` if a hook is present (critic finding #12 — the previously
   dead protocol method now has its invocation site: authority + challenge have passed, no op has run yet;
   the release-testing band uses this to arm a test-mode trace).
6. `return await apply_draft(draft, decision, preview, confirmation, …)`.

**Error / failure modes** (all classified through `from_exception` ①, landing on the frozen §2.7 outcomes):

| Exception | `error_class` / `reason` | §2.7 outcome |
|---|---|---|
| `UndraftableOperation(op_kind)` — no registered op-kind binding | `user_error` / `USER_ERROR` | `BLOCKED` (at add) |
| `DraftNotFound(draft_id)` | `user_error` / `NOT_FOUND` | `BLOCKED` |
| `DraftClosed(draft_id, status)` — mutate/apply a terminal draft | `user_error` / `USER_ERROR` | `BLOCKED` |
| `StalePreview(expected, actual)` — `preview_hash` ≠ draft's current (op set changed) | `user_error` / `USER_ERROR` | `BLOCKED` (re-preview required) |
| `AcceptDenied` — `resolve_draft_accept` denied any distinct ref | `denied` / `AUTHORITY` | `BLOCKED` (K6 `denial_message`) |
| `ConfirmDeclined` — `requires_confirmation` and challenge unmet/mismatched | `user_error` / `CONFIRM_DECLINED` | `DECLINED` |
| a per-op `engine.run` failure | classified by the engine → per-op `WorkflowResult` | draft `PARTIAL` (or propagated outcome) |

---

## 4. Provides / Consumes

### Provides (owned canonical shapes — everyone else consumes these)

| Shape | Where | Consumers |
|---|---|---|
| `Draft`/`DraftOperation`/`OwnerScope` primitive keyed `(producer, owner_scope, draft_id)` | `sb/spec/draft.py` | Final Review, AI orchestration (rung-4), C-3 preset instantiation, release-test flow |
| Fail-closed `OpKindRegistry` + `OpKindBinding` (the ONE `op_kind → WorkflowRef/schema/is_resource_create` key) | `sb/kernel/draft/registry.py` | the pipeline; the composition root (registers each draftable op_kind's K7 workflow) |
| `derive_accept_authority` + `resolve_draft_accept` (AND-over-distinct-refs; Accept authority for non-setup producers) | `sb/kernel/draft/accept.py` | the pipeline; the panel action that renders the Accept button |
| `DraftPreview`/`DraftConfirmationSpec`/`PreviewContext` — the **batch** aggregation of §2.7's single-op shapes | `sb/kernel/draft/preview.py` | the Final Review / confirm renderer |
| `ConfirmationResponse` + `verify_confirmation` (the kernel-verified challenge gate) | `sb/spec/draft.py` / `preview.py` | the Accept/confirm surface (passes the user's typed/button response) |
| `AcceptHook` port + `VerificationContext` (test-mode / `verified_live` plug-point) | `sb/spec/draft.py` | the release-testing-loop band (concrete hook), Q-0234/Q-0222 sign-off store |
| `apply.dedup_token` definition (completes ④.2 skeleton): `f"{draft_id}:{op_seq}"`, supplied to K7 via `ctx.params["_draft_dedup_token"]` | `sb/kernel/draft/apply.py` | the K7 per-op `once()` guard (K3 idempotency substrate) |

### Consumes (assumed sibling shapes — exact assumption stated)

| Shape | Assumed source | Exact assumption |
|---|---|---|
| `authority_ref`, `AuthorityRequest`, `AuthorityDecision`, `resolve_authority`, `owner_override_holds` | K6 / spec 04 (frozen ②) | `resolve_authority(req)->AuthorityDecision` with the fixed step order; `owner_override_holds(user_id, is_member)` member-gated; TIERS total-ordered `user<…<owner`; every CAPABILITY ref ⇒ administrator floor (v1). `AuthorityDecision.actor` carries the resolved `ActorRef` (used to build the per-op WorkflowContext). |
| error envelope: `from_exception`, `Result`, `DenialReason` | K8 / spec 02 (frozen ①) + `sb/spec/outcomes.py` | `from_exception(exc, surface, target, section_label)->ErrorEnvelope`; `DenialReason` incl. `CONFIRM_DECLINED`, `NOT_FOUND`, `AUTHORITY`, `USER_ERROR`. |
| **`WorkflowEngine.run(spec, ctx)` / `.preview(spec, ctx)`** returning `WorkflowResult` / `MutationPreview`; `refs.resolve(workflow_ref) -> CompoundOpSpec` | **K7 workflow engine (`07-workflow-engine.md`, WRITTEN sibling)** | 07 §3.2: `async run(spec: CompoundOpSpec, ctx: WorkflowContext) -> WorkflowResult` (opens its OWN `db.transaction()` per op, 07 §3.3 step 4; emits ONE central audit row, 07 §3.4; per-op `once()` if the spec declares `DURABLE_ONCE`, using `dedup_key.render(ctx)` — I supply `_draft_dedup_token`); `async preview(spec, ctx) -> MutationPreview` (txn-rollback + skip-effects). **Two `WorkflowContext` fields this pipeline requires — `correlation_id: str \| None` and `test_mode: bool` — are seam-corrections flagged for 07 (§12).** **07 also declares external-conn PURE-DB entries `run_ref(ref, ctx, *, conn)` / `apply(…)`, fenced `atomic_db_only` and reserved for pure-DB callers (09 scheduler `ManagedTaskSpec` handlers; invariant `repair_refs` / version `compensation_refs`) — NOT this pipeline's ops. A draft resource-create op bears a post-commit Discord EFFECT leg (outside the `atomic_db_only` fence), so it stays on `run(spec, ctx)` per-op (§3.5); cross-op shared-txn atomicity is a structural boundary for the draft lane resolved by caller type, not a pending K7 co-decision (§12).** |
| audit-row semantics: `emit_audit_action` (11 fields) + `audit_log.correlation_id` COLUMN | ③ (shipped `audit_events.py:52`) + K7 §5 / 08 §5.1 | K7 emits **one central row per op** (07 §3.4); I supply `correlation_id = draft_id` via `ctx.correlation_id`, written into the **nullable `correlation_id` column already added by 07 §5 and 08 §5.1** (the 11-field `emit_audit_action` bus payload is UNCHANGED — the correlation rides the column, not a 12th field; §12). |
| `IdempotencyKey`, `once`/`record_outcome`/`read_outcome`, `db.transaction()` | K3 / spec 05 (frozen ④/⑤) | consumed **transitively through K7** — apply_draft never calls `once()` directly; K7 does, keyed on the `_draft_dedup_token` I pass. `namespace` reserved per op_kind's `op_key` (K1). |
| `MutationPreview`/`WorkflowResult`/`ConfirmationSpec` single-op shapes, `classify_outcome`, `StepResult`, reversibility constants | §2.7 / lifecycle `contracts.py` | verbatim per the frozen §0/§2.7; `WorkflowResult` is the K7 design superset of shipped `LifecycleResult:77` (no shipped class). |
| `ManagedTaskSpec`/`PollLane` host for the `ExpiryJanitorLane` | 09-scheduler-state §3.6/§4 | 09 hosts `ExpiryJanitorLane` (wraps `store.select_expired(now) → update_status(EXPIRED)` + the stuck-`APPLYING` sweep) on its `PollSupervisor` — this pipeline supplies the read primitives, 09 owns the write cadence. |
| `PanelActionSpec.confirm` + the kernel action callback | §2.6 | the Accept button is a `PanelActionSpec` whose `handler` is a `WorkflowRef` into `confirm_and_apply`, passing the user's `ConfirmationResponse`; **cooldown/audit parity on the button is SF-a/L-5 — panel-owned, not mine.** |

---

## 5. Data model + migration / index shape

Fresh chain `0001` (§5.2 — no legacy carry). Two tables:

```
sb_drafts
  draft_id            uuid  PRIMARY KEY
  producer            text  NOT NULL            -- Producer enum value
  owner_guild_id      bigint NOT NULL
  owner_actor_id      bigint                    -- NULL for system/backfill (list query uses IS NOT DISTINCT FROM)
  status              text  NOT NULL            -- DraftStatus enum value
  accept_authority_ref text NOT NULL            -- derived DISPLAY/LIST floor (the gate is per-ref AND, §3.4)
  correlation_id      uuid  NOT NULL            -- = draft_id; propagated to each op's audit_log.correlation_id
  verification_json   jsonb                     -- VerificationContext | NULL
  created_at          timestamptz NOT NULL
  updated_at          timestamptz NOT NULL
  expires_at          timestamptz               -- NULL = no TTL
  INDEX (owner_guild_id, owner_actor_id, status)   -- list_open_drafts (NULL-safe predicate at query time)
  INDEX (status, expires_at)                       -- ExpiryJanitorLane select_expired sweep (09)

sb_draft_operations
  draft_id            uuid  NOT NULL REFERENCES sb_drafts(draft_id) ON DELETE CASCADE
  op_seq              int   NOT NULL            -- 1-based order; the 10-channel fix
  op_kind             text  NOT NULL            -- the OpKindRegistry key
  subsystem           text  NOT NULL
  authority_ref       text  NOT NULL
  payload_json        jsonb NOT NULL
  label               text  NOT NULL
  dedup_token         text  NOT NULL            -- default f"{draft_id}:{op_seq}"; the K7 per-op once() token
  PRIMARY KEY (draft_id, op_seq)               -- identity is (draft, order) — NO slot-key collapse
```

`is_resource_create` and the preview provider are **not columns** — both are DECLARED properties on the
`OpKindBinding` (§3.3), resolved by `op_kind` at preview/apply time. Persisting them per row would
duplicate registry truth and drift.

**Dedup / idempotency key (the apply-time durable guard, ④):** rows in the shared `idempotency_keys`
table (K3), written **by K7** (not this pipeline) under `key = "{op_key}:{guild_id}:{dedup_token}"`,
`dedup_token = f"{draft_id}:{op_seq}"` (default). A producer needing cross-draft dedup (a preset
re-instantiated) may override `DraftOperation.dedup_token` with a stable natural key. **The
`(draft_id, op_seq)` PK is the structural fix for L-7's collapse** — op identity is *position in the
draft*, never a `(op_kind, subsystem, setting, binding)` slot, so N `create_channel` ops persist as N rows.

Importer (§5.2): live `setup_draft_operations` rows are transient staging, not ledger data — **not
imported**; drafts open at cutover are dropped (the operator re-stages). No alias map needed.

---

## 6. Restart & merge=deploy behavior

| Concern | Behavior |
|---|---|
| **Draft durability** | Drafts are **durable DB rows** — survive a merge=deploy restart. (Confirmations are session-scoped per ⑤ — a restart drops the confirm *prompt*; the actor re-opens Final Review, re-previews, re-confirms with a fresh `ConfirmationResponse`. `preview_hash` catches an op set that changed in between.) |
| **Boot reconcile** | **No auto-apply on boot** — drafts are user-initiated, never scheduled, so unlike the scheduler (⑤.3) the draft pipeline arms nothing at boot. The only crash-visible state is `status=APPLYING`: **09's stuck-`APPLYING` lane** (a registered `PollLane` on 09's one `PollSupervisor`, 5 s cadence, 09 §3.7) calls `db.draft.reap_stuck_applying(now, DRAFT_APPLY_STUCK_TTL_S)` — a **strictly-conditional compare-and-set** (`UPDATE … SET status='partial' WHERE status='applying' AND updated_at < now() - ttl`), so it can flip **only** an `APPLYING` row that has not progressed for the whole TTL. A live-but-slow multi-channel apply keeps its `updated_at` fresh (the per-op heartbeat, §3.5 step 2) and is therefore **never reaped mid-flight**. Either way the operator's re-run is safe because K7's per-op `once()` skips already-applied ops. |
| **Exactly-once (per pure-DB op)** | Each op's DB legs are guarded **by K7** with `once(IdempotencyKey(op_key, guild_id, f"{draft_id}:{op_seq}"))` **inside K7's own `db.transaction()`** (④.1 canonical pattern). A confirm delivered to both gateway connections during fast-release overlap (⑤.4), or a re-run after a crash mid-apply, applies each pure-DB op **exactly once**; the second attempt `read_outcome`s and skips. **Resource-create EFFECT legs are best-effort, not exactly-once** — see the Atomicity row. |
| **Dual-instance overlap** | Both workers live sub-second during fast-release. In-session double-click dedup is the in-memory `request_id` (④.2); the **durable** guard across instances is K7's per-op `once()`. No draft-level lock is needed — per-op `once()` covers it uniformly (the same reason ⑤.4 fast-release is correct). |
| **Atomicity across restart** | **Per-op, not cross-op.** Each op is one K7 `db.transaction()` — a restart mid-op rolls that op back (nothing half-written); its re-run re-applies cleanly and later ops resume. Earlier committed ops stay committed (the draft is a sequenced idempotent batch, not one transaction — §3.5). Resource creates run as K7 post-commit EFFECT legs: a restart may leave a created channel; a crash *between* the external create and its outcome record can **orphan or duplicate** it (the DB guard does not cover the external effect) — reconciliation rides the compensation deferral (§9). |
| **Expiry** | `store.select_expired(now)` (READ) yields non-terminal drafts past `expires_at`; **09's `ExpiryJanitorLane`** writes the `EXPIRED` transition under its poll (09 §3.7/§4). The old "OR lazily at `load_draft`" alternative is deleted — `load_draft` is a read-only primitive and must not mutate status. |

**Stuck-`APPLYING` TTL — `DRAFT_APPLY_STUCK_TTL_S = 900` (15 minutes).** The reaper's age threshold is
pinned *comfortably above* the worst-case honest apply, so the conditional CAS can only ever catch a genuine
crash and never a live apply:

- **Worst case in the capability corpus** is the flagship **10-channel canary** (and larger `PRESET`
  instantiations). Each op is one K7 `run(spec, ctx)` — a short DB txn plus one post-commit Discord create
  EFFECT leg. Discord channel-creates are per-route rate-limited; even a burst of a few dozen creates with
  rate-limit backoff and a bounded retry completes in **well under 60 s**, and a pathological preset of a few
  hundred ops still finishes in a small number of minutes.
- **15 minutes is >10× that ceiling.** Combined with the per-op heartbeat (§3.5 step 2), the TTL measures
  *time since the last op progressed*, not wall-clock apply length — so even an unusually large draft cannot
  age out **while it is making progress**. Erring long is safe by construction: recovery is **cosmetic** (the
  re-run is idempotent via K7's per-op `once()`), so a crashed `APPLYING` reaped a few minutes late costs
  nothing, whereas a live apply reaped early would falsely strand a good draft as `PARTIAL`. At the 5 s poll
  cadence a genuinely stuck row is cleaned within one poll after it crosses the TTL.
- The reaper is a **conditional CAS**, and `apply_draft`'s success write is the matching conditional
  `update_status(APPLIED, expect=APPLYING)` (§3.5 step 5) — so in the vanishing race where a completing apply
  and the reaper touch the same row, exactly one write wins and the loser is a safe no-op that re-reads the
  authoritative status. Never a blind overwrite in either direction.

---

## 7. Architecture rules honored (INV / layer cites)

- **DB access only through the `utils.db.*` boundary** — all SQL lives in `sb/kernel/db/draft.py`
  (asyncpg only); `sb/kernel/draft/*` never calls `pool.execute()`. (CLAUDE.md DB-access rule; INV-mirror
  of `utils/db/` → asyncpg-only layer.)
- **All mutations through the domain `*_mutation.py` seam** — `apply_draft` **never writes a domain row
  itself**; it delegates every write to the K7 workflow engine (`engine.run(spec, ctx)`), which routes
  through the audited `settings_mutation`/`binding_mutation`/`resource_provisioning`/governance seams
  (`test_pipeline_audit_wiring.py:24`). The draft pipeline is a *staging + orchestration* layer, not a
  writer.
- **All auditable mutations call `emit_audit_action`** — satisfied transitively: each op's central audit
  row is emitted **inside** the workflow engine (③.1, "never bypassed by the resolver/orchestrator");
  apply_draft only supplies the `correlation_id`. Draft create/edit/discard is staging, not an auditable
  mutation, so it correctly emits none.
- **`services` must NOT import `views` (zero-tolerance)** — `sb/kernel/draft/*` (kernel/service tier)
  imports no view; the Final Review view imports the pipeline, never the reverse. The apply seam moves
  **out of** `views/setup/final_review.py` (a view holding apply logic today) into the kernel — a
  layering *improvement*.
- **`settings_keys` constants, never raw keys** — a `set_setting` op's `payload` carries a
  `SettingSpec`-declared key (validated at add against the binding's `payload_schema`); the draft store
  never invents a raw key string.
- **cogs never import cogs** — N/A (kernel). Producers (AI cog, setup cog) each import the pipeline, not
  each other.
- **Compile fence (③.4 `audit_completeness`)** — every op_kind whose effect is `mutating` binds to a
  `WorkflowRef` (the audited engine) in its `OpKindBinding`; a draftable op_kind that mapped to a bare
  `HandlerRef` is a `SEMANTIC_VIOLATION` at compile. The fail-closed registry enforces the runtime half:
  no binding ⇒ un-draftable.

---

## 8. Options → Decision → Why (each fork closed)

| Fork | Options | Decision | Why |
|---|---|---|---|
| **Op identity** | (a) slot key `(op_kind,subsystem,setting,binding)` [shipped] · (b) `(draft_id, op_seq)` | **(b)** | (a) is the exact L-7 collapse — 10 create_channel ops → 1 row. Position-in-draft is the natural identity for an ordered op list and makes the 10-channel draft representable. |
| **Store cardinality** | (a) one row per guild [shipped singleton] · (b) many drafts per guild keyed `draft_id` | **(b)** | Two producers (human + AI) must coexist without destructive merge (C-2 "one pipe, two producers"). `draft_id` PK + `(guild,actor,status)` index gives per-actor listing. |
| **Op-kind slot missing** | (a) cosmetic "preflight unavailable" label [shipped `no_adapter`] · (b) **fail-closed: op is un-draftable** | **(b)** | A draft you can't preview is a draft you can't safely confirm. Fail-closed makes "un-previewable ⇒ un-confirmable" a structural guarantee, not operator vigilance. |
| **Op → executable binding** | (a) per-op `preview_provider` ProviderRef + a name-prefix `is_resource_create` · (b) **one `OpKindRegistry` keyed by `op_kind`, binding `WorkflowRef` + `payload_schema` + declared `is_resource_create`** | **(b)** | (a) had TWO ambiguous keys (the op's `preview_provider` field vs `op_kind`) and a fragile prefix rule. One registry keyed by `op_kind` resolves preview (K7 `preview(spec)`), apply (K7 `run(spec)`), payload schema, and the resource-create hint from a single declared binding. (Closes critic findings #6/#8/#10.) |
| **`preflight_operations` fate** | (a) wire it as the preview provider · (b) **delete it, port its diff logic into K7 `preview()`** | **(b)** | It is env-gated dead code with zero consumers; its real value (the current/proposed read for bind/set_setting) is exactly what the workflow engine's per-lane `preview()` must compute anyway. One preview path, not two. |
| **Accept authority** | (a) hard-wired setup-admin [shipped] · (b) fixed per-producer · (c) union-max to one string · (d) **derived DISPLAY floor + AND over every distinct op `authority_ref` as the gate** | **(d)** | (c) silently strips a capability op's revoke overlay in a mixed draft (a revoked role could Accept a setup-containing draft — critic #14). AND-over-distinct-refs vetoes on any single revoked ref; the derived string stays a display badge only. |
| **Confirm mandate + enforcement** | (a) always confirm · (b) never · (c) T2-5 rule but flag-only · (d) **T2-5 rule + a fail-closed apply gate (`verify_confirmation` + `confirmed` threaded to K7)** | **(d)** | Computing `requires_confirmation` without gating it is the L-5 "charge once, run freely" class. The gate at §3.5 step 1 + the `confirmed` flag into K7's own confirm-assert (07 §3.3 step 2) makes confirmation structural. (Closes critic #2/#7.) |
| **Apply atomicity granularity** | (a) call it "atomic" for everything · (b) **per-op-atomic via K7 `run(spec)` + idempotent resume; Discord-create = K7 post-commit EFFECT leg (best-effort)** · (c) one shared txn across all pure-DB ops | **(b)** | (c) cannot apply to the draft lane: a cross-op pure-DB txn would ride `run_ref`'s `atomic_db_only` fence, and draft resource-create ops bear a post-commit EFFECT leg that the fence excludes (07 §3.3 — effect-bearing ops enter via per-op `run(spec, ctx)`). (a) is dishonest for non-rollback-able creates (D-1..D-6). (b) is buildable NOW on K7's real API and honest about the EFFECT-leg best-effort boundary (T2-1). The *word* "atomic" for the resource lane is surfaced below. |
| **Cross-op shared transaction** | (a) per-op txn via `run(spec, ctx)` · (b) one shared txn across pure-DB ops via 07's external-conn `run_ref(ref, ctx, *, conn)` | **(a) — for the draft lane it is the ONLY eligible entry, not a fallback** | 07 **does** expose `run_ref`/`apply` (external-conn, pure-DB), but they are fenced `atomic_db_only` and serve 09's scheduler + the invariant/version pure-DB callers. The draft's ops bear post-commit Discord EFFECT legs → **outside** that fence → they can only enter via `run(spec, ctx)` per-op. So (b) is **structurally unavailable** to this pipeline (not a pending co-decision); the F-2 fork resolves cleanly by caller type. Built = per-op-atomic + idempotent resume. |
| **Build-now vs deferred behind C-1** | (a) build on the shipped singleton seam · (b) **fresh `sb/` primitive, sequenced after K7/K8** | **(b)** | The primitive is a *new* kernel function (L-7 says "not a port"); building on the singleton would inherit the collapse. It consumes K7 `run()` + K8 error envelope, so it sequences **after** them (K9), not "behind C-1" as a blocker — C-1 (the resolver) and C-2 (this) are peers over the same engine/authority substrate. |
| **Draft-level lock** | (a) advisory lock per draft · (b) **per-op `once()` only (K7-owned)** | **(b)** | ⑤.4's lesson: `once()`+`db.transaction()` covers overlap uniformly; a draft lock adds a failure mode (stuck lock on crash) that `once()` doesn't have. |

---

## 9. Labeled deferrals (each bounded by the capability corpus)

| Deferral | Reason | Bound |
|---|---|---|
| **Cross-op shared-transaction atomicity** | 07 **does** expose the external-conn `run_ref(ref, ctx, *, conn)` / `apply` entries, but they are fenced `atomic_db_only` and serve pure-DB callers (09 scheduler; invariant `repair_refs` / version `compensation_refs`). Draft ops bear a post-commit Discord EFFECT leg, so they are outside that fence — a whole-draft shared pure-DB txn is **structurally unavailable** to this lane, not merely un-built. | Per-op-atomic + idempotent resume (§3.5) is the **final** semantics for effect-bearing draft ops (not a pending upgrade). Any all-or-nothing need across ops is met at the *recovery* layer (the compensation deferral below), never by a shared txn. |
| **Test-mode effect routing to a real test guild** | The built default suppresses real Discord EFFECT writes under `test_mode` (fail-safe: never touch a real guild). True end-to-end verification against a live test guild is the release-testing band's + the L-10 test data-plane's (vocab §⑥.3). | `VerificationContext.test_mode` threads into every op's `WorkflowContext.test_mode`; the concrete "suppress vs route-to-test-guild" behavior is owned by the release-testing band behind the `AcceptHook` + L-10 data-plane seam. Safe default built now. |
| **Stuck-`APPLYING` recovery ownership** | A crash between step 2 and step 5 leaves `APPLYING`; the re-run is already safe via K7's `once()`, so recovery is cosmetic. | 09 owns the *cadence* (its stuck-`APPLYING` `PollLane`, 09 §3.7); this pipeline supplies the **conditional-CAS DB primitive** `reap_stuck_applying(now, ttl_s)` it calls (`WHERE status='applying' AND updated_at < now() - ttl`, §3.2) with `DRAFT_APPLY_STUCK_TTL_S = 900` s comfortably above a worst-case multi-channel apply (§6) — so a slow-but-live apply is never reaped. |
| **Cross-draft preset dedup** | Default `dedup_token=f"{draft_id}:{op_seq}"` dedups within a draft; a preset re-instantiated twice creates twice. | The `dedup_token` override field already exists (§3.1) — a producer sets a stable natural key when it wants cross-draft idempotence. No schema change. |
| **Compensation/undo of a partial batch (incl. orphaned resource creates)** | Full saga/rollback of created Discord resources is out of the C-2 corpus (A#26 "record without a saga engine"). | The `PARTIAL` result records what applied; K7's `compensator` seam (07 §3.3 step 5) records left-behind/orphaned effects; a compensation *engine* is a later band. |
| **Concurrent edits to one draft** | Two admins editing the same `draft_id` — last-write-wins on `updated_at`, and `preview_hash` catches a stale confirm. | The optimistic `preview_hash` gate is built now; a pessimistic per-draft edit lock is deferred (rare; two admins share `owner_scope`). |
| **Draft-level audit trail** | Whether draft *staging* (not apply) is itself audited. | Apply is fully audited (N central rows correlated by `draft_id`, §3.5). Staging audit rides SF-c (dispatch-trace promotion) if the owner wants it; default: none. |

---

## 10. Retirement map

| Item | Source | How this spec retires it |
|---|---|---|
| **L-7 · per-guild singleton** | FJ §2 | `sb_drafts` keyed `draft_id`; many drafts per guild; `(producer, owner_scope)` columns — two producers coexist, no destructive merge. **Retired.** |
| **L-7 · unrepresentable 10-channel** | FJ §2 | op identity = `(draft_id, op_seq)`; 10 `create_channel` ops persist as 10 rows. **Retired.** |
| **L-7 · Accept hard-wired to setup-admin** | FJ §2 | `resolve_draft_accept` = AND over every distinct op `authority_ref` through K6 (mixed-draft-safe); owner-override applies uniformly. **Retired.** |
| **L-7 · dead `preflight_operations` diff (zero consumers)** | FJ §2 / verified | deleted; diff logic ports into K7 `preview(spec, ctx)` behind the fail-closed op-kind registry. **Retired.** |
| **T2-1 · atomic-apply meaning for non-rollback-able Discord ops** | FJ §6 (A#1) | per-op-atomic via K7 `run(spec)`; resource creates = K7 post-commit EFFECT legs (best-effort, NOT exactly-once); cross-op all-or-nothing is **structurally** off the table for the draft lane — 07's external-conn `run_ref`/`apply` shared-txn entry is fenced `atomic_db_only` and the draft's ops bear EFFECT legs, so they enter via `run(spec, ctx)` per-op (§8 / §12). The word "atomic" for the resource lane is owner-gated → open decision. **Reconciled with 07's per-op DB/EFFECT model; F-2 resolved by caller type.** |
| **T2-5 · which actions MUST use preview/confirm** | FJ §6 (C2-Q4) | `requires_confirmation`: destructive ∨ AI-produced ∨ bulk/compound; single reversible direct-lane exempt — **and structurally gated** at apply via `verify_confirmation` + the `confirmed` flag into K7. **Retired (encoded + enforced).** |
| **T2-19 · native Discord onboarding / server-template interop** | FJ §6 (B#9) | The draft primitive is **independent of** Discord-native onboarding/server-templates; a `PRESET` producer MAY emit ops mirroring a server template, but the draft is our own primitive with our own preview/confirm/audit. Interop is one-directional (we can *read* a template into ops; we never delegate apply to Discord's template engine). Boundary documented → **retired as a documented boundary.** |
| **§4 gap: C-2 "not new architecture" claim re-baselined** | FJ §4 (L-7 lead-in) | §1 states plainly: C-2 **is** new architecture (the singleton can't carry a second producer). The conventions §2.4 "already-designed draft lane" line is corrected. |
| **③.3 correlation seam — one row vs N per compound apply** | vocab ③.3 / 07 §8 fork B | Resolved by the **nullable `correlation_id` COLUMN** already on `audit_log`/`outbox` (07 §5, 08 §5.1); this pipeline supplies `correlation_id = draft_id` via `ctx.correlation_id`. The only residual is the `WorkflowContext.correlation_id` FIELD to carry it (seam-correction for 07, §12). **Resolved by column; plumbing flagged.** |
| **Owner-queue: test-mode `verified_live` sign-off has no mechanism** | release-testing-loop D / Q-0234 / Q-0222 | `VerificationContext` + `AcceptHook.on_confirmed`/`on_applied` plug-points named + invoked; `test_mode` threads into K7 with a fail-safe suppress default; concrete test-guild routing deferred to the release-testing band. **Plug-point retired; audience/routing owner-gated → open decision.** |

---

## 11. Build order (K-placement + what it blocks)

**Placement: K9** — the draft/preview/confirm/apply pipeline, a strand-2 kernel function.

**Depends on (must land first):** K3 (idempotency `once`/`record_outcome` + `db.transaction()`, spec 05,
consumed transitively through K7) · K6 (authority engine `resolve_authority`, spec 04) · K7 (**workflow
engine `run(spec, ctx)` / `preview(spec, ctx)`** — the WRITTEN sibling `07-workflow-engine.md`, plus the
two flagged `WorkflowContext` fields §12) · K8 (error envelope `from_exception`/`Result`, spec 02) · K2
(the ref table resolving `WorkflowRef → CompoundOpSpec`) · K1 (op-kind token reservation + each op_kind's
`op_key` idempotency namespace).

**Peers (share the K3 substrate, no dependency):** the outbox (08) and the scheduler (09) — all three
consume ④'s `IdempotencyKey` + `db.transaction()`; the draft-expiry sweep rides **09's** `PollSupervisor`
as a registered `ExpiryJanitorLane` (09 §4).

**Blocks (cannot ship until this lands):**
- **Rung-4 AI orchestration** (conventions §2.4 — the `AI_ORCHESTRATION` producer; the D&D 10-channel canary).
- **C-3 template instantiation** (a preset is a `PRESET`-producer draft feeding this pipeline).
- **The release-testing loop D** (`verified_live` sign-off via the `AcceptHook` plug-point).
- **The setup wizard Final Review port** (becomes a thin surface over `DraftPipeline`).
- **Fuzzy/NL destructive actions** (rung-2/3 route their confirm through this, not a bespoke path).

**Internal build order:** (1) `sb/spec/draft.py` leaf → (2) `sb/kernel/db/draft.py` + migration `0001x` →
(3) `sb/kernel/draft/store.py` → (4) `sb/kernel/draft/registry.py` (`OpKindRegistry` + `OpKindBinding`) →
(5) `sb/kernel/draft/preview.py` (batch shapes + `PreviewContext` + `verify_confirmation`, over K7
`preview(spec)`) → (6) `sb/kernel/draft/accept.py` (AND-over-refs) → (7) `sb/kernel/draft/apply.py` (the
per-op loop over K7 `run(spec)`) → (8) `pipeline.py` facade → (9) register each draftable op_kind's
`OpKindBinding` in the composition root; retire the six shipped paths (§2); register the `ExpiryJanitorLane`
on 09's supervisor.

---

## 12. Seam notes flagged for the sibling specs (do not silently diverge)

1. **Correlation seam — RESOLVED by column, one field of plumbing remains (was the stale §12 fork).** The
   old open decision ("add a 12th `emit_audit_action` field OR encode `draft_id` into `target`/`scope`")
   is **withdrawn** — siblings already resolved it the third way: `audit_log` (07 §5) and `event_outbox`
   (08 §5.1) both carry a **nullable `correlation_id uuid` COLUMN**, set only when ④ (this pipeline)
   invokes N ops as one draft apply. The 11-field `emit_audit_action` bus payload stays frozen. The one
   mechanical gap: **K7's `WorkflowContext` has no field to carry `draft_id` in, and `WorkflowResult` none
   to read it out.** Seam-correction for 07: add `correlation_id: str | None = None` to `WorkflowContext`
   (apply_draft sets it = `draft_id`) and have K7's central-audit DB leg write `ctx.correlation_id` into
   the reserved column. This is mechanical — 07 §8 fork B already assigns ④ the N-invocation loop + id.
2. **`test_mode` field on `WorkflowContext` (seam-correction for 07).** A `RELEASE_TEST` draft must not
   fire a real Discord write against a real guild. `test_mode` is distinct from `dry_run` (dry_run rolls
   the DB back; test_mode COMMITS the DB test but suppresses/routes the external EFFECT legs). K7's
   `WorkflowContext` needs `test_mode: bool = False`, and its EFFECT-leg runner (07 §3.3 step 5) must honor
   it — built default: **suppress the real Discord write and render the planned effect to
   `VerificationContext.debug_channel_id`**. The richer route-to-a-real-test-guild behavior is the
   release-testing band's (§9). Flagged so 07 does not treat test_mode as merely `dry_run`.
3. **Engine entry reconciliation (was the "K7 DOES NOT YET EXIST" assumption).** This pipeline now targets
   07's REAL declared API — `run(spec: CompoundOpSpec, ctx)` / `preview(spec: CompoundOpSpec, ctx)`, per-op
   self-txn, one central audit row per op. There is no **per-`DraftOperation`** entry `engine.apply(op, *,
   conn)` — 07's `apply(…)` is the pure-DB, `atomic_db_only`-fenced external-conn sibling of `run_ref` (item
   4), consumed by the scheduler/invariant callers, never by this pipeline's op loop. Every earlier call site
   is rewritten to resolve each op → a `CompoundOpSpec` → `run(spec, ctx)` (§3.3/§3.5).
4. **Engine-entry split — F-2 RESOLVED (no open co-decision remains for this pipeline).** 07 declares
   **both** entries: `run(spec, ctx)` (per-op self-txn + post-commit EFFECT legs) **and** the external-conn
   `run_ref(ref, ctx, *, conn)` / `apply(…)` (fenced `atomic_db_only`). The F-2 fork resolves **by caller
   type, not by adding an entry**: this pipeline's draft ops are **EFFECT-bearing** (a post-commit Discord
   create), which `run_ref`'s `atomic_db_only` fence excludes, so **draft ops go through `run(spec, ctx)`
   per-op** and a cross-op shared pure-DB txn is structurally unavailable to the draft lane. `run_ref`/`apply`
   exist for the **pure-DB** callers that legitimately use them — 09's scheduler `ManagedTaskSpec` handlers,
   and the invariant `repair_refs` / version `compensation_refs`. **Seam note for 07:** its `atomic_db_only`
   fence must scope to the `run_ref`/`apply` callers **only** — it must **not** list any draft `op_kind`
   mapping in scope, because draft ops legitimately carry EFFECT legs and enter via `run(spec, ctx)`. No
   shared K7 co-decision is left open for this pipeline; **06's per-op semantics win the reconciliation.**

---

*Written 2026-07-04 against the frozen shared vocabulary (`../shared-vocabulary.md`, all-five-pass) and
reconciled against the three WRITTEN strand-2 siblings (`07-workflow-engine.md`, `08-event-outbox.md`,
`09-scheduler-state.md`). Spot-verified against shipped source this session: `utils/db/setup_draft.py`
(whole), `views/setup/final_review.py:60-94,659-701`, `services/setup_operations.py:194,362,803`,
`services/setup_change_plan.py:174-221` (zero consumers), `services/audit_events.py:52` (11 keyword-only
fields), `services/lifecycle/contracts.py:40-52/56/66/77/108`, `tests/unit/services/
test_pipeline_audit_wiring.py:24`; `class WorkflowResult` and `disbot/core/contracts.py` re-confirmed
ABSENT. **NOT SOURCE OF TRUTH for runtime** — a Phase-B design contract for the strand-2 build to execute
against.*
