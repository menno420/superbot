# Strand-2 · ⑤ The Workflow / Compound-Op Engine (K7) — Buildable Design Spec

> **Status:** `reference` — foundational design artifact (2026-07-04). **NOT SOURCE OF TRUTH** — a design contract; shipped source + the frozen upstream contracts win (Q-0120).

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B design contract. Precedence: shipped source &
> merged PRs > the five strand-1 specs (for shapes they own) > the frozen `shared-vocabulary.md` >
> this doc. This doc **builds on** the frozen vocab (`../shared-vocabulary.md` §①–⑩) and **completes**
> the skeletons it left for K7: the compound-audit-row semantics (③.3), the per-action idempotency
> posture (④ / T2-21), and the LegSpec/CompoundOpSpec/engine-entry contract that does not yet exist
> anywhere. Spot-verified against shipped source this session (cites inline). Design against frozen
> decisions Q-0219…Q-0237 — never re-decided here.
>
> **Source-wins grounding (Q-0120), re-verified this session.** There is **no shipped `WorkflowResult`
> class** and **no `disbot/core/contracts.py`** — both are design-spec-only names (vocab §0). The **real**
> result-grammar seams are `disbot/services/lifecycle/contracts.py`: `LifecycleResult` (`:77`),
> `LifecyclePreview` (`:66`), `StepResult` (`:56`), the five outcome constants (`:48-52`), the three
> reversibility constants (`:40-42`) — all verified this session. The shipped **dispatch-result analogue**
> is `StageResult` (`disbot/core/runtime/message_pipeline.py:181`), which never crosses `resolve()` and is
> **not** the design dispatch return. K7's `WorkflowResult` is the **design superset** of the shipped
> `LifecycleResult` (design §2.7) that K7 *lands* — spec-only, never a shipped class.

---

## 1. Summary + the exact undesigned gap

**What K7 is.** The single audited seam through which every *multi-write* mutation runs. A domain
declares a **CompoundOpSpec** (ordered **LegSpec**s + one `authority_ref` + a declared idempotency
posture + one central audit verb); the engine runs the DB legs inside **one** `db.transaction()`,
writes **one central audit row** keyed by `mutation_id`, runs external/Discord legs *after* commit,
and returns a **`WorkflowResult`** (the design superset of `LifecycleResult`, §0). It exposes **three
co-designed entries over one internal core** (§3.2) so every named consumer reaches it through the
seam it needs: `run()` (self-owned txn — the resolver `INVOKE_WORKFLOW` target, verified
`02-resolver-error-envelope.md:218`, **and the draft pipeline's per-op entry** — the draft resolves each
`DraftOperation` → `CompoundOpSpec` and calls `run()` **per op**, each in its OWN txn,
`06-draft-pipeline.md:451-466`), `run_ref(ref, ctx, *, conn=…)` (the external-conn fire for the scheduler's
`ManagedTaskSpec.handler`, the invariant `repair_refs`, and version `compensation_refs`,
`09-scheduler-state.md:389,491`), and `apply(op, *, conn)` (the op-kind → spec external-conn **sibling** of
`run_ref`, declared per 06's expectation — **NOT** the draft's live entry).

**Already designed (anti-pad — I do not re-derive these):**
- `WorkflowResult` / `MutationPreview` / `ConfirmationSpec` **field sets are fully specified** in
  design-spec **§2.7** (superset of shipped `LifecycleResult:77` / `LifecyclePreview:66`, reusing
  `StepResult:56` + the `:40-42`/`:48-52` constants verbatim). I **adopt** them and the `from_*`
  adapters as-is; K7 *lands* them but authors nothing new about their shape. **The step-7 constructor
  (§3.3) is illustrative of *population*, not the authoritative field list — the field list is design
  §2.7's** (which carries `cache_invalidated` and the typed `source` tag beyond the ten
  `LifecycleResult` fields).
- The idempotency primitives `once`/`record_outcome`/`read_outcome` + the `idempotency_keys` table +
  the `db.transaction()` seam are **owned by K3** (`05-ops-kernel-rails.md:389-429`, frozen vocab §④).
  I **consume**, never redefine, them.
- `resolve_authority` / `AuthorityDecision` / `authority_ref` are **owned by K6** (frozen vocab §②). I
  **consume** them as leg-0 of every op.
- `emit_audit_action`'s 11-field payload is **shipped** (`audit_events.py:52`, verified) and frozen
  (vocab §③.2) — I never edit it. The **durable twin** `enqueue_audit_action(conn,…)` is **owned by the
  outbox sibling** (`08-event-outbox.md:150`, seam-correction §12 #2); I **consume** it for the central
  bus trace (§3.4) so the `audit.action_recorded` event is crash-durable, not best-effort.
- `DeliveryClass` is **owned by the outbox sibling** at `sb/spec/events.py` (canonical home, `08` §12
  seam-correction #1); K7's `EventEmitSpec.delivery` **imports** it — one enum, no drift (§3.1, absorbs
  the correction the sibling flagged against this doc's earlier local `class DeliveryClass`).
- `ConfirmationSpec` is a **manifest spec leaf** read by the compiler (K1/K2) at compile time; it lives
  in `sb/spec/confirmation.py`, **not** the K7 kernel band. K7's `result.py` re-exports it (§2).

**The genuinely undesigned gap this spec closes (all K7-owned):**

| Undesigned today | What this spec delivers |
|---|---|
| ~66 hand-rolled `db.transaction()` sites across the domain services (per-file **totals**: mining 21, fishing 16, game-wager 6, ticket 5, farm 4, treasury 3, … — **~48 are multi-leg**, the subset this engine targets first), each re-choreographing acquire→txn→N writes→commit→emit **differently** | **`LegSpec` + `CompoundOpSpec` + `run()`/`run_ref()`/`apply()`/`preview()`** — the one declarative engine that replaces them |
| No declared idempotency on the accrual faucets — **farm-collect double-credits on deploy overlap** (verified `farm_workflow.py:114-179`: no `once()`, no dedup key) | **`IdempotencyPosture`** (T2-21 mandate) + compiler fence; farm-collect becomes `DURABLE_ONCE` |
| farm-collect **audits only the coin leg** (`credit_in_txn`→`insert_economy_audit`); the coop-reset and XP legs leave **no audit trail** | **One central `audit_log` row per compound-op**, all legs as sub-detail (completes vocab §③.3) |
| No dry-run for money/state workflows — only `automation_executor` has the invariant (`automation_executor.py:10-14`) | **`preview()`** = txn-rollback + skip-effect-legs, the structural dry-run oracle, generalized |
| The audit-row-granularity fork (③.3) and the "atomic-apply" fork (T2-1) are open skeletons | Closed structurally (LegKind DB/EFFECT split; one-row-per-invocation; external-conn seam) — §8 |

**Named canary:** `economy.farm.collect` — the smallest end-to-end compound op (credit + reset + XP,
3 legs, an empty-state no-op, and the double-credit bug the posture fixes). Its dry-run oracle is the
Gate-V acceptance test for the whole engine.

---

## 2. Files / modules it becomes

**New (`sb/kernel/workflow/`, layer = kernel; imports utils, core-substrate, `sb/spec/*`, `sb/kernel/db/*`,
`sb/kernel/outbox/*`, `kernel/authority/*` — **never** cogs/views):**

| Path | Owns |
|---|---|
| `sb/kernel/workflow/spec.py` | `LegSpec`, `LegKind`, `CompoundOpSpec`, `IdempotencyPosture`, `DedupKeySpec`, `LegAuditSpec`, `EventEmitSpec`, `EmptyResultSpec`, `WorkflowLane`. **Imports** `DeliveryClass` from `sb/spec/events.py` (not defined here — §12 #1) and `ConfirmationSpec` from `sb/spec/confirmation.py`. |
| `sb/kernel/workflow/registry.py` | `WorkflowRegistry` — `register(spec)` keyed by `op_key`; `resolve(ref: WorkflowRef) -> CompoundOpSpec`; `resolve_op_kind(op_kind: str) -> CompoundOpSpec` (the draft `DraftOperation.op_kind → spec` map). The single place a `WorkflowRef`/draft-op resolves to its `CompoundOpSpec`. |
| `sb/kernel/workflow/context.py` | `WorkflowContext` (incl. `correlation_id`), `LegOutcome`, the typed `LegHandler` protocol |
| `sb/kernel/workflow/result.py` | `WorkflowResult`, `MutationPreview`, `PlannedStep`, `FieldChange` (design §2.7 — adopted) + the `from_settings/…/from_treasury` adapters; **re-exports** `ConfirmationSpec` from `sb/spec/confirmation.py` |
| `sb/kernel/workflow/audit.py` | the **audit spine**: `emit_central_audit()` over the durable twin `enqueue_audit_action` (§3.4) + the `audit_log` DB leg (§5) |
| `sb/kernel/workflow/engine.py` | `run(target, ctx, *, dry_run=False) -> WorkflowResult` · `run_ref(ref, ctx, *, conn=None) -> WorkflowResult` · `apply(op, *, conn) -> WorkflowResult` · `preview(target, ctx) -> MutationPreview` — the three entries + the dry-run oracle over ONE internal core (`_execute`) |
| `sb/kernel/workflow/compile.py` | the three K7 compiler fences: `idempotency_posture_declared`, `audit_completeness` (mutating ref ⇒ `WorkflowRef`, vocab §③.4), `atomic_db_only` (§3.6) |

**Retired shipped paths** (bodies become LegSpec/CompoundOpSpec declarations + registered leg handlers
in `domain/<x>/`):

| Shipped file | Multi-leg `db.transaction()` sites → CompoundOpSpecs |
|---|---|
| `services/farm_workflow.py:114-179` | `collect` → `economy.farm.collect` (the canary) + `buy`/`upgrade` |
| `services/mining_workflow.py` (21 sites, e.g. `:1324-1358`) | `dig`/`equip`/`repair`/… |
| `services/fishing_workflow.py` (16) · `services/creature_workflow.py` (2) · `services/skill_service.py` (2) | idle/checkpoint game ops |
| `services/game_wager_workflow.py:89-…` (6) | `open_pvp_wager`/`settle_pvp`/`refund_pvp`/`enter_tournament`/`payout_tournament` — the escrow family (INV-F) |
| `services/shop_purchase_workflow.py:60-98` · `services/treasury_service.py` (3) · `services/ticket_mutation.py` (5) | direct-lane compound ops |
| `services/economy_service.py:196-259` (`transfer`) + `:289-327` (`bet_and_settle`) | become **leg handlers** — `transfer`'s raw `conn.execute` (`:253`, a shipped `utils.db` violation) is retired: legs call `utils.db.*` only |

---

## 3. The complete public contract

### 3.1 The declared shapes (manifest; every field `[S]` unless tagged)

```python
# sb/kernel/workflow/spec.py
from sb.spec.events import DeliveryClass          # CANONICAL home is the outbox leaf (§12 #1) — imported, not defined here
from sb.spec.confirmation import ConfirmationSpec  # manifest leaf, compile-time readable (K1/K2) — not a K7 kernel type

class LegKind(enum.Enum):
    DB     = "db"      # runs inside the single db.transaction() conn; rolled back atomically on failure
    EFFECT = "effect"  # runs AFTER commit; external/Discord/event; NOT rolled back (compensating|record-only)

class WorkflowLane(enum.Enum):                 # the WorkflowResult.lane tag (design §2.7)
    SCALAR="scalar"; BINDING="binding"; RESOURCE="resource"
    GOVERNANCE="governance"; LIFECYCLE="lifecycle"; DOMAIN="domain"

class IdempotencyPosture(enum.Enum):           # T2-21 — the MANDATED per-op declaration
    DURABLE_ONCE   = "durable_once"    # once()+record_outcome over idempotency_keys (K3) — double-fireable ops; REQUIRES dedup_key
    NATURAL_KEY    = "natural_key"     # effect is intrinsically once (ON CONFLICT / FOR UPDATE row-consumption, e.g. escrow) — no guard row
    SINGLE_FLIGHT  = "single_flight"   # in-process lock only (single-process, ADR-001); REQUIRES single_flight_scope; reproduce NOT required
    NONE_JUSTIFIED = "none"            # explicitly non-idempotent; REQUIRES idempotency_justification (read-only / truly at-most-once)

# DeliveryClass (imported): AT_LEAST_ONCE  → written as an outbox row INSIDE the txn; relay delivers post-commit
#                           BEST_EFFORT    → emitted after commit; a drop is a log line (shipped default)

@dataclass(frozen=True)
class DedupKeySpec:
    # EITHER a registered token handler(ctx)->str (for a computed token),
    # OR a tuple of ctx.params names the engine joins by ":" (for a natural key, e.g. ("user_id","interaction_id")).
    source: WorkflowRef | tuple[str, ...]      # [S]
    def render(self, ctx: "WorkflowContext") -> str:
        # tuple form: ":".join(str(ctx.params[name]) for name in self.source) — KeyError iff a named param is absent
        #             (a compile fence asserts every named param is a declared op input).
        # WorkflowRef form: the registry-resolved handler(ctx) -> str.
        ...

@dataclass(frozen=True)
class LegAuditSpec:                            # OPTIONAL per-leg enrichment folded into the ONE central row
    audit_target_kind: str                     # [S] "balance" | "coop" | "inventory" | "gear" …
    verb: str                                  # [S] leg verb token (detail only; the central row uses op.audit_verb)

@dataclass(frozen=True)
class EventEmitSpec:
    event: str                                 # [S] frozen legacy event name (e.g. economy_service.EVT_BALANCE_CHANGED)
    payload_builder: WorkflowRef               # [S] handler(ctx, result)->dict; reads only fields present at step 4b (see §3.3)
    delivery: DeliveryClass                    # [S] the imported enum

@dataclass(frozen=True)
class EmptyResultSpec:                          # the "nothing to do" no-op (farm-collect: settled.eggs<=0)
    predicate: WorkflowRef                      # [S] handler(ctx)->bool, evaluated BEFORE the txn opens
    user_message: str                          # [S] the no-op copy

@dataclass(frozen=True)
class LegSpec:
    leg_id: str                                # [S] namespace-reserved leg token, unique within the op
    kind: LegKind                              # [S]
    handler: WorkflowRef                       # [S] registered LegHandler
    reversibility: str                         # [S] shipped constant (REVERSIBLE|COMPENSATABLE|IRREVERSIBLE, contracts.py:40-42) — the PER-LEG author declaration
    compensator: WorkflowRef | None = None     # [S] REQUIRED iff kind==EFFECT and reversibility==COMPENSATABLE
    audit: LegAuditSpec | None = None          # [S]
    optional: bool = False                     # [S] a failed optional leg degrades the op to PARTIAL, never BLOCKED

@dataclass(frozen=True)
class CompoundOpSpec:
    # --- required (no default) — declared first so the dataclass is valid ---
    op_key: str                                # [S] namespace-reserved workflow key ("economy.farm.collect") — also the once() namespace on the standalone lane
    domain: str                                # [S] audit subsystem
    lane: WorkflowLane                         # [S]
    authority_ref: str                         # [S] resolved as leg-0 (consumes K6)
    legs: tuple[LegSpec, ...]                  # [S] ordered; DB legs run in-txn first, EFFECT legs after commit
    idempotency: IdempotencyPosture            # [S] T2-21
    dedup_key: DedupKeySpec | None             # [S] REQUIRED iff idempotency==DURABLE_ONCE (else None)
    audit_verb: str                            # [S] mutation_type for the ONE central row
    # --- optional / conditionally-required (fence-enforced, §3.6) — all defaulted ---
    idempotency_justification: str | None = None  # [S] REQUIRED iff idempotency==NONE_JUSTIFIED; else MUST be None
    single_flight_scope: str | None = None     # [S] REQUIRED iff idempotency==SINGLE_FLIGHT; the in-process lock key (e.g. f"{op_key}:{user_id}"); else None
    confirmation: ConfirmationSpec | None = None   # [S] presence — NOT keyed on reversibility (§3.3 step 2)
    emits: tuple[EventEmitSpec, ...] = ()      # [S] post-commit events
    empty_result: EmptyResultSpec | None = None    # [S]
    reversibility: str = ""                    # [derived — NOT [S]] engine computes max(leg reversibilities); author never sets it (§3.6)
```

**`reversibility` is derived, not declared (§3.6 fence).** The **per-leg** `LegSpec.reversibility` is
the author's `[S]` declaration; the **op** rollup is `max(leg.reversibility for leg in legs)` under the
total order `REVERSIBLE < COMPENSATABLE < IRREVERSIBLE` (`contracts.py:40-42` order). The author leaves
`CompoundOpSpec.reversibility` unset; the compiler computes + freezes it and asserts the confirm rule
(`op.reversibility==IRREVERSIBLE` **and** `confirmation is None` ⇒ `COMPILE_ERROR`, honoring design §2.7
/ 01 P6). No author/engine disagreement is possible because the author never sets it.

### 3.2 The engine entry + leg protocol

```python
# sb/kernel/workflow/context.py
@dataclass(frozen=True)
class WorkflowContext:
    actor: ActorRef                            # from K8 ResolveRequest (has member_tier — RC-12); consumed
    guild_id: int
    request_id: str                            # confirm re-entry dedup (in-memory, vocab §④.2)
    confirmed: bool = False                    # set by the resolver on the re-entrant confirm dispatch (02 step 5)
    dry_run: bool = False                       # set by preview()
    correlation_id: str | None = None          # set ONLY by ④ (= draft_id) when N ops are one draft apply; threaded into the audit_log row (§3.4/§5)
    params: Mapping[str, object] = field(default_factory=dict)   # typed op inputs (user_id, interaction_id, item_name, price, …)
    clock: Clock = SYSTEM_CLOCK

@dataclass(frozen=True)
class LegOutcome:
    step: StepResult                           # shipped :56 (target_id, target_name, ok, error)
    before: object | None = None               # structured prior value → central-row prev_value + diff
    after: object | None = None                # structured new value  → central-row new_value + diff
    payload: object | None = None              # typed value the op result surfaces (e.g. new_balance)
    warnings: tuple[str, ...] = ()

class LegHandler(Protocol):
    # conn is the txn-bound Connection for DB legs; None for EFFECT legs (post-commit).
    async def __call__(self, conn: Connection | None, ctx: WorkflowContext) -> LegOutcome: ...

# sb/kernel/workflow/engine.py — THREE co-designed entries over ONE internal core (_execute).
async def run(target: "WorkflowRef | CompoundOpSpec", ctx: WorkflowContext, *,
              dry_run: bool = False) -> WorkflowResult: ...
#   Resolves a WorkflowRef→CompoundOpSpec (registry). Opens its OWN db.transaction() and owns
#   once()/record_outcome (namespace=op_key). Runs DB legs + EFFECT legs + BEST_EFFORT emits.
#   THE resolver INVOKE_WORKFLOW target (02 step 5) + the standalone/canary path.

async def run_ref(ref: "WorkflowRef", ctx: WorkflowContext, *,
                  conn: "Connection | None" = None) -> WorkflowResult: ...
#   Resolves ref→spec (registry). conn is None ⇒ delegates to run(spec, ctx). conn provided ⇒
#   EXTERNAL-CONN mode: runs the DB legs + central audit + AT_LEAST_ONCE enqueue on the CALLER's conn,
#   opens NO txn, calls NO once()/record_outcome (caller owns dedup), runs NO EFFECT/BEST_EFFORT
#   (caller owns commit). The external-conn fire for the scheduler ManagedTaskSpec.handler (09:389,491),
#   the invariant repair_refs, and version compensation_refs (09:228). NOT the draft entry — the draft
#   runs each DraftOperation through run() per-op (06 §3.5).

async def apply(op: "DraftOperation", *, conn: "Connection") -> WorkflowResult: ...
#   The op_kind→spec external-conn SIBLING of run_ref: maps op.op_kind→CompoundOpSpec
#   (registry.resolve_op_kind), then behaves as run_ref EXTERNAL-CONN mode on the caller's conn. Declared
#   per 06's expectation (06:25-28) and atomic_db_only-fenced identically to run_ref. NOT the draft's live
#   entry — the draft resolves each DraftOperation → CompoundOpSpec and calls run(spec, ctx) PER-OP (own
#   txn per op, 06 §3.5); apply stays for op-kind external-conn dispatch.

async def preview(target: "WorkflowRef | CompoundOpSpec", ctx: WorkflowContext) -> MutationPreview: ...
#   == run(target, ctx, dry_run=True), projected to MutationPreview (§3.5).
```

**Why three entries, one core.** All three consumers need the *same* leg execution + central audit, but
differ on **who owns the txn and the dedup guard**:

| Entry | Owns the txn? | Owns `once()`? | Runs EFFECT legs? | Consumer |
|---|---|---|---|---|
| `run()` | **engine** (`db.transaction()`) | **engine** (namespace=`op_key`) | yes (post-commit) | resolver `INVOKE_WORKFLOW` (02 step 5); **the draft's per-op apply** (06 §3.5 — each `DraftOperation` → its `run()` txn); standalone/canary |
| `run_ref(conn=…)` | **caller** | **caller** (caller's namespace, e.g. scheduler `task_key`) | no — pure-DB + AT_LEAST_ONCE emits only (`atomic_db_only`) | scheduler `_fire` (09:389); invariant `repair_refs`; version `compensation_refs` (09:228) |
| `apply(op, conn)` | **caller** | **caller** (caller's namespace) | no — pure-DB + AT_LEAST_ONCE emits only | the op-kind → spec external-conn **sibling** of `run_ref` (declared per 06; **not** the draft's live entry) |

The external-conn entries deliberately do **not** open a txn or call `once()`: the caller (the scheduler's
fire txn; the invariant/version repair-compensation txn) owns a single `db.transaction()` around the
`run_ref` call and owns the guard row under its own namespace (avoiding a double-`once()`). This is exactly
what `09-scheduler-state.md:389,491` (the `_fire` target) and `09`'s version-reject compensation (`:228`)
consume. **The draft pipeline is NOT an external-conn caller** — it resolves each `DraftOperation` →
`CompoundOpSpec` and calls `run(spec, ctx)` **per op** (own txn per op, `06-draft-pipeline.md:451-466`),
because draft resource-create ops carry a post-commit Discord EFFECT leg that the `atomic_db_only` fence
excludes from the external-conn path. The earlier single-entry `run(spec, ctx)` (self-txn only) was
structurally incompatible with the scheduler's external `conn` — resolved by `run_ref`; the draft, by
contrast, resolves to `run()` per-op (F-2 resolved by caller type, §8 fork A).

**Dispatch-dedup co-ownership (no double-`once()`).** For `INVOKE_WORKFLOW`, the engine's `run()`
`once()` (namespace=`op_key`) **is** the workflow-lane dispatch dedup (vocab §④.2) — the resolver
delegates the workflow-lane guard to the engine rather than running a second `once()` under a command
namespace. One guard row per invocation.

### 3.3 The algorithm (buildable, zero further decisions)

**`run()` — the self-owned-txn path** (the external-conn variant differs only where noted):

| # | Step | Rule / failure mode |
|---|---|---|
| 0 | **empty-state** | if `spec.empty_result` and its predicate holds ⇒ return `WorkflowResult(outcome=SUCCESS, steps=(), committed_at=None, user_message=empty.user_message)`. **No txn, no audit, no dedup.** (farm-collect's `eggs<=0`.) |
| 1 | **authority** | `d = await resolve_authority(AuthorityRequest(spec.authority_ref, actor…))`; `not d.allowed` ⇒ `WorkflowResult(outcome=BLOCKED, reason=AUTHORITY, user_message=d.denial_message)`. **Return.** |
| 2 | **confirm backstop** | keyed on **presence, not reversibility** (matches resolver 02 step 5 + design §2.7): `if spec.confirmation is not None and not ctx.confirmed:` raise `ConfirmRequired`. On the **resolver path** the resolver's own step-5 confirm gate fires *before* dispatch, so `run()` never actually sees an unconfirmed confirm-bearing op — step 2 is the **backstop for headless callers**. `ConfirmRequired` is a **typed control signal, NOT a `from_exception` input** (vocab §①.2): a headless caller (scheduler/draft, no confirm round-trip) catches it in `_execute`'s wrapper and maps it to `WorkflowResult(outcome=BLOCKED, reason=CONFIRM_DECLINED, user_message="This action needs interactive confirmation and can't run unattended.")`. (A compile fence additionally forbids a `confirmation`-bearing spec from being an **external-conn** caller — a scheduler `ManagedTaskSpec.handler` / invariant `repair_ref` / version `compensation_ref` — §3.6; a **draft** `op_kind` MAY carry a `confirmation` because the draft runs it through `run()` per-op, which honors this confirm gate.) |
| 3 | **mint + key** | `mutation_id = uuid4()`. `DURABLE_ONCE` ⇒ `key = IdempotencyKey(namespace=op_key, guild_id, dedup_token=spec.dedup_key.render(ctx))`. `SINGLE_FLIGHT` ⇒ acquire the in-process lock keyed by `spec.single_flight_scope` (released in `finally`). |
| 4 | **txn** | `async with db.transaction() as conn:` (K3). **a) guard** — `DURABLE_ONCE`: `if not await once(key, conn=conn): return _reproduce(await read_outcome(key, conn=conn))` (§3.7 — the no-op replay; may block on the guard row until the first txn commits, then reproduces; never double-effects). **b) DB legs** — run in order, `conn`-bound, collecting `LegOutcome`s. A **required** DB leg raising is caught in-txn, classified via **`from_exception(exc, surface=Surface.MAINTENANCE, target=None)`** (02) to an `ErrorEnvelope`, and the txn is aborted by re-raising an internal `_AbortTxn(envelope)` sentinel — the outer wrapper **catches it and RETURNS** `WorkflowResult(outcome=envelope.outcome, reason=envelope.reason, user_message=envelope.user_message)` (BLOCKED for user_error/denied/bug, DISCORD_FAILED for transient). **The `MAINTENANCE`/`None` inputs are the buildable K7 error path (PIN-4):** 02 adds the `Surface.MAINTENANCE` background member and widens `from_exception`'s `target` to `TargetRef | None`, and K7 is the surface-agnostic composition layer holding **no** interaction `TargetRef`, so it classifies under the ONE background surface with `target=None`. Because `surface`/`target` only enrich `user_message` while the classifier core (`error_class`→outcome/reason) is surface/target-independent (02 §3.3), `MAINTENANCE`/`None` yields the class's canonical copy verbatim; on the interactive resolver path the resolver's own step-5 `from_exception` (with the real surface/target) renders the user-facing copy, so K7's generic copy is only surfaced on a headless (scheduler / invariant-repair) leg failure. `Surface` is imported from `sb/kernel/interaction/request.py` (02 §2). **`run()` does not re-raise classified failures** (the error-return contract, §3.3-note). An **optional** DB leg raising ⇒ record `step.ok=False`, continue, op → PARTIAL. **c) build pending result** — assemble the in-txn `pending = WorkflowResult(mutation_id, …, outcome=so-far, before, after, steps, committed_at=None)` so `payload_builder(ctx, pending)` has every field it may read (the ordering fix — the final result at step 7 only *adds* `committed_at` + effect-leg outcomes). **d) central audit** (§3.4) — the `audit_log` DB row + the durable `enqueue_audit_action(conn, …)` bus trace, both in-txn. **e) AT_LEAST_ONCE emits** — `batch = await outbox.enqueue_all(spec.emits, ctx, pending, conn=conn)`: each `AT_LEAST_ONCE` emit is written as an outbox row **now** (in-txn); each `BEST_EFFORT` emit is appended to the returned `BestEffortBatch` for post-commit (§3.4). **f) record** — `DURABLE_ONCE`: `await record_outcome(key, outcome, result_ref=mutation_id, conn=conn)`. **g) dry_run** ⇒ raise `_DryRunRollback` (nothing persists; §3.5). |
| 5 | **effect legs** (post-commit) | run **EFFECT legs** (`conn=None`). Fail + `COMPENSATABLE` ⇒ run `compensator`, op → PARTIAL; fail + `IRREVERSIBLE` ⇒ record an operator finding, op → PARTIAL/DISCORD_FAILED. (Skipped entirely under `dry_run`.) |
| 6 | **best-effort emit** (post-commit) | `await batch.emit_after_commit()` — `bus.emit`s the `BEST_EFFORT` events captured at step 4e. (Skipped under `dry_run`.) |
| 7 | **return** | finalize the step-4c `pending` with `committed_at`, effect-leg outcomes, `audit_emitted`, `event_emitted`, warnings. The **authoritative field list is design §2.7's** `WorkflowResult` (superset of `LifecycleResult`: `{mutation_id, guild_id, domain, operation=op_key, outcome, reversibility, steps, lane, before, after, committed_at, audit_emitted, event_emitted, cache_invalidated, source, warnings, user_message}`). |

**Error-return contract (closes the raise-vs-return divergence).** `run()`/`run_ref()`/`apply()`
**catch every *classified* leg failure, roll the txn back, and RETURN a `WorkflowResult`** on the frozen
five outcomes — they never propagate a classified error to the caller. This is exactly what the draft
(`06 §3.5` — each per-op `engine.run(spec, ctx)` failure → classified → per-op `WorkflowResult` → draft
PARTIAL) consumes: the per-op loop keeps going. The resolver's step-5 "exceptions → `from_exception`" path (02) is therefore
reserved for a **truly-unexpected escape** (an engine-internal bug that is not a leg failure) — the two
consumers are now consistent.

**External-conn variant (`run_ref(conn=…)` / `apply`).** Same steps **0–4e** on the **caller's** `conn`,
with two differences: step 4a is **skipped** (the caller already ran `once()` under its namespace before
calling — 09 `_fire` (`:389`) / the invariant-repair / version-compensation callers (`:228`)) and step 4f
is **skipped** (the caller owns `record_outcome`). Steps 5 and 6 are **not run** — the caller owns commit,
so EFFECT legs and `BEST_EFFORT` emits have no post-commit home; the `atomic_db_only` fence (§3.6)
guarantees an external-conn spec is pure-DB with `AT_LEAST_ONCE` (in-txn, durable) emits only. The returned
`WorkflowResult` is the step-4c pending finalized with `committed_at=None` (the caller's commit stamps
durability); `mutation_id` is present for the caller's `record_outcome(result_ref=result.mutation_id)`.
(The draft pipeline does **not** use this variant — it calls `run()` per-op, §3.2.)

### 3.4 The central audit row (completes vocab §③.3; closes the L-9 central-trace gap)

**One CompoundOpSpec invocation ⇒ exactly one `audit_log` DB row** (§5) + **exactly one
`audit.action_recorded` bus event** (the trace `server_logging._on_audit_action` consumes). Both are
written **inside** the step-4 txn by a kernel-appended DB leg:

- **The `audit_log` row** — `mutation_id`-keyed, `mutation_type=op.audit_verb`, `prev_value`/`new_value`
  the rollup of leg `before`/`after`, `correlation_id = ctx.correlation_id` (set only by ④ — §5), the N
  legs as `detail` JSONB + `WorkflowResult.steps`. **Never** N rows.
- **The bus trace — durable, not best-effort (the L-9 fix for the central event).** The engine emits via
  the outbox sibling's **durable twin `enqueue_audit_action(conn, …)`** (`08:150`, seam-correction §12 #2)
  when the `audit.action_recorded` event is declared `AT_LEAST_ONCE` (the recommended v1 posture, §8/§9):
  the event row is captured **in-txn**, so a crash after commit but before the relay ticks does **not**
  lose the central trace — the relay redelivers the identical 11-field `audit.action_recorded` event
  post-commit, and `server_logging._on_audit_action` is untouched. If the owner leaves the event
  `BEST_EFFORT`, the engine falls back to the shipped post-commit `emit_audit_action` (failure-safe,
  returns `False`, DB authoritative). **This supersedes the earlier "central trace = best-effort
  `emit_audit_action`" wording**, which left the L-9 gap the outbox sibling exists to close.

Per-leg `LegAuditSpec` enriches `detail`; it does **not** emit a second row. This is the §③.3 "batched
lifecycle op ⇒ 1 row" generalized to every compound op.

### 3.5 `preview()` — the dry-run oracle

`preview(target, ctx)` runs `run(target, ctx, dry_run=True)` and projects the result. It runs step 0-1
(empty-state, authority) then the txn with `dry_run=True`: DB legs run (handlers may honor `ctx.dry_run`
to compute-without-writing; **or they write and the engine's `_DryRunRollback` at step 4g rolls the whole
txn back** — the rollback is the structural teeth), collecting `planned_steps` + `diff`. It **skips EFFECT
legs and best-effort emit** (the `automation_executor.py:10-14` invariant: "when dry_run no Discord-side
side effect happens"), **never** calls `enqueue_audit_action`/`emit_audit_action`, `once`, or
`record_outcome`, and returns `MutationPreview(allowed, operation, summary, reversibility, planned_steps,
diff, warnings, requires_confirmation)`. **Guarantee (the oracle):** after `preview()`, DB state is
byte-identical and zero Discord/effect calls fired — the Gate-V acceptance assertion for every op.

### 3.6 The three compiler fences (`compile.py`)

- **`idempotency_posture_declared`** — every mutating `CompoundOpSpec` MUST declare `idempotency`
  (T2-21). It **also** enforces the posture's mandated field: `DURABLE_ONCE ⇒ dedup_key is not None`;
  `NONE_JUSTIFIED ⇒ idempotency_justification is not None` (and non-`NONE_JUSTIFIED` ⇒ it is `None`);
  `SINGLE_FLIGHT ⇒ single_flight_scope is not None`; a `DedupKeySpec` tuple `source` ⇒ every named token
  is a declared op input. A missing posture or mandated field is `SEMANTIC_VIOLATION` → CI-red.
- **`audit_completeness`** — a spec with `effect="mutating"` MUST carry a `WorkflowRef` (= a
  `CompoundOpSpec`), else `SEMANTIC_VIOLATION` → CI-red (vocab §③.4). Also derives + freezes
  `op.reversibility = max(leg reversibilities)` and asserts `IRREVERSIBLE ⇒ confirmation is not None`.
- **`atomic_db_only`** — the predicate the external-conn seam relies on. Its scope is the **external-conn
  `run_ref`/`apply` callers ONLY**: **every `CompoundOpSpec` reachable as a scheduler
  `ManagedTaskSpec.handler` `WorkflowRef`, an invariant `repair_ref`, or a version `compensation_ref`** —
  **NOT** a draft `op_kind` mapping (draft ops route through `run()` per-op, the unconstrained
  EFFECT-legs-allowed lane, §3.2). For every in-scope spec, assert: **(1)** every leg is `kind==DB` (no
  `EFFECT` legs — the caller owns commit, so no post-commit leg can run); **(2)** every DB-leg handler's
  import closure touches only `utils.db.*` + the domain `*_mutation.py` seams — **no** `discord`,
  `aiohttp`, `EventBus.emit`, or other external I/O inside a DB leg (an AST import-closure check); **(3)**
  every `emit` is `AT_LEAST_ONCE` (or absent) — no `BEST_EFFORT` emit on the external-conn path (it would
  have no post-commit home); **(4)** `confirmation is None` (a headless external-conn spec cannot
  round-trip a confirm). Any violation is `SEMANTIC_VIOLATION` → CI-red. Ops invoked via `run()` — **the
  resolver lane AND the draft's per-op apply** — are unconstrained: they may carry EFFECT legs,
  BEST_EFFORT emits, and confirmations. **This scoping is load-bearing (PIN-2 / F-2):** the flagship
  10-channel resource-create draft carries a post-commit Discord `create_channel` EFFECT leg per op — were
  `atomic_db_only` to reach draft `op_kind` specs it would reject every such op as CI-red (an `EFFECT` leg
  on the external-conn path). So the draft *must* run each op through `run()` per-op (EFFECT legs allowed),
  and the fence *must not* scope to the draft.

### 3.7 `_reproduce(PriorOutcome)` — the deduped-replay result

On a `DURABLE_ONCE` double-fire, `once()` returns `False` and the engine reproduces the first result from
the durable record without re-effecting. `PriorOutcome` carries only `{outcome, result_ref, first_seen_at}`
(vocab §④.1), where `result_ref == mutation_id`. `_reproduce`:
1. re-reads the `audit_log` row by `mutation_id = prior.result_ref` (the durable spine, §5) to recover
   `prev_value`/`new_value`/`detail`/steps of the first invocation;
2. constructs `WorkflowResult(mutation_id=prior.result_ref, outcome=prior.outcome, before/after/steps` from
   the recovered row, `committed_at=` the row's `occurred_at`, `user_message=` a generic idempotent-replay
   copy ("This action was already completed."));
3. runs **no** EFFECT legs and **no** emit (the effects fired on the first pass).

The deduped second surface (the L-6 double-gateway delivery) thus renders the idempotent-replay copy, not
a second money credit — the concrete farm-collect fix. (If the first txn is still mid-flight,
`read_outcome` may return `None`; the guard row is row-locked until it commits, so step 4a blocks on it,
then reproduces — never a partial replay.)

---

## 4. Provides / Consumes

**Provides (owned canonical shapes strand-2 / games / draft consume):**

| Shape | Consumer |
|---|---|
| `LegSpec` · `CompoundOpSpec` · `IdempotencyPosture` · `DedupKeySpec` · `WorkflowRegistry` | every mutating domain (Phase 4); the compiler fences |
| `run()` (the `INVOKE_WORKFLOW` target + the draft's per-op entry) | resolver 02 step 5; **the draft pipeline ④** — `apply_draft` resolves each `DraftOperation` → `CompoundOpSpec` and calls `run(spec, ctx)` **per-op** (own txn per op; 06 §3.5); the panel engine (renders `preview()`) |
| `run_ref(ref, ctx, *, conn)` (external-conn fire) | the scheduler `_fire` (09:389) — runs the leg set in the scheduler's own txn under the scheduler's `once()`; the invariant `repair_refs` / version `compensation_refs` (09:228) |
| `apply(op, *, conn)` (external-conn op-kind sibling of `run_ref`) | declared per 06's expectation (06:25-28) for op-kind external-conn dispatch; `atomic_db_only`-fenced identically to `run_ref` — **NOT** the draft's live entry (the draft uses `run()` per-op) |
| `preview()` | the draft's per-op `preview` (06 §3.4); the panel confirm renderer |
| the central-audit-row contract (one row + one durable bus event per op, `mutation_id`, legs as detail) | `server_logging._on_audit_action`; the operator audit log |
| `WorkflowResult` (landed here) | resolver `Result.workflow`; the golden harness ("new-as-old") |

**Consumes (assumed sibling shapes — exact assumption stated):**

| Shape | Owner | Exact assumed contract |
|---|---|---|
| `IdempotencyKey`, `once`/`record_outcome`/`read_outcome`, `db.transaction()`, `idempotency_keys` | **K3 / spec 05** | `once(key,*,conn)->bool` (INSERT…ON CONFLICT DO NOTHING RETURNING); `record_outcome`/`read_outcome` same txn (`05:389-429`); `transaction()` yields a `conn.transaction()`-bound Connection (verified `pool.py:170-182`) |
| `resolve_authority`, `AuthorityRequest`, `AuthorityDecision.{allowed,denial_message}` | **K6 / spec 04** | vocab §② — leg-0; the engine passes `ctx.actor.member_tier` (RC-12) |
| `from_exception(exc, *, surface, target)->ErrorEnvelope` + `Result` | **spec 02** | vocab §① — every classified leg exception routes through **`from_exception(exc, surface=Surface.MAINTENANCE, target=None)`** (K7 is surface-agnostic and holds no interaction `TargetRef`; **buildable via 02/PIN-4** — the `Surface.MAINTENANCE` background member + `target: TargetRef \| None`); `error_class`→outcome per the frozen table; `surface`/`target` only enrich `user_message` (the classifier core is surface-independent, 02 §3.3), so `MAINTENANCE`/`None` yields the class's canonical copy. `ConfirmRequired` is **not** an input (§3.3 step 2 — a control signal mapped directly to BLOCKED/CONFIRM_DECLINED). `Surface` imported from `sb/kernel/interaction/request.py` (02 §2) |
| `emit_audit_action(**11 fields)` (best-effort fallback) | **shipped `audit_events.py:52`** | vocab §③.2 — the `BEST_EFFORT` central-row emit; failure-safe (returns False; DB authoritative). Never edited |
| `enqueue_audit_action(conn, **11 fields)` (durable twin) + `enqueue_all(emits, ctx, result, *, conn) -> BestEffortBatch` + `BestEffortBatch.emit_after_commit()` | **strand-2 outbox (L-9/T2-3), `08:150,161,169`** | the durable central-trace emit + the in-txn AT_LEAST_ONCE writer; `enqueue_all` returns the best-effort batch the engine emits post-commit at step 6 |
| `DeliveryClass` (imported enum) | **strand-2 outbox, `sb/spec/events.py`** | canonical home (§12 #1); `EventEmitSpec.delivery` imports it — never a local copy |
| `ConfirmationSpec` (imported spec leaf) | **`sb/spec/confirmation.py` (K1/K2 leaf)** | compile-time-readable by `CommandSpec/PanelActionSpec.confirm` + 01 P6; `result.py` re-exports it |
| `StepResult:56`, `LifecycleResult:77`, reversibility/outcome constants `:40-52` | **shipped `services/lifecycle/contracts.py`** | reused verbatim (design §2.7); `WorkflowResult` is the design superset (§0) |
| `DraftOperation` (`op_kind`, `payload`, `dedup_token`) | **draft pipeline, spec 06 §3.2** | the type `apply(op, conn)` — the op-kind external-conn **sibling** of `run_ref` — maps to a `CompoundOpSpec` via `registry.resolve_op_kind`. **The draft's own apply loop does NOT call `apply`** — it resolves each `DraftOperation` → `CompoundOpSpec` and calls `run(spec, ctx)` per-op (06 §3.5); this row is the op-kind dispatch shape `apply` retains |
| `ChallengeSessionSpec.escrow` / `IdleAccrualSpec.collect_workflow` (`WorkflowRef`) | **design §2.8 game facet** | each resolves to a `CompoundOpSpec`; escrow ports the `game_wager_workflow` family (see seam-correction), accrual-collect ports the farm/mining pattern |

---

## 5. Data model + migration / index shape

**Consumes (no new table):** `idempotency_keys` (K3) — `key(PK) · namespace · first_seen_at ·
outcome(nullable until `record_outcome`) · result_ref`. K7 writes it only via `once`/`record_outcome` on
the **standalone** (`run()`) lane; on the external-conn lanes the **caller** writes it.

**Owns (the audit spine, K7 band):** `audit_log` — the cross-domain central row.

```
audit_log (
  mutation_id     uuid        PRIMARY KEY,      -- the once()-guarded write key; a replay never re-inserts
  subsystem       text        NOT NULL,
  mutation_type   text        NOT NULL,         -- op.audit_verb
  target          text        NOT NULL,
  scope           text        NOT NULL,         -- 'global' | 'guild'
  guild_id        bigint      NULL,
  prev_value      text        NULL,             -- rollup of leg before-states
  new_value       text        NULL,             -- rollup of leg after-states
  actor_id        bigint      NULL,
  actor_type      text        NOT NULL,
  occurred_at     timestamptz NOT NULL,
  detail          jsonb       NOT NULL DEFAULT '{}',  -- per-leg StepResults + FieldChanges (the N-leg sub-detail)
  correlation_id  uuid        NULL              -- = ctx.correlation_id (= draft_id) when ④ invokes N ops as one apply (§8 fork B)
)
```
Indexes: `(guild_id, occurred_at DESC)` (operator log) · `(subsystem, mutation_type, occurred_at DESC)`
(forensics) · `(correlation_id) WHERE correlation_id IS NOT NULL` (draft-apply grouping).

**`correlation_id` — a DB-spine column, populated from `WorkflowContext.correlation_id`; the 11-field bus
payload is UNCHANGED.** ④ sets `ctx.correlation_id = draft_id`; the central audit DB leg (§3.4) writes it
into this column, so the operator forensic log groups the N rows of one draft apply. The **frozen 11-field
`emit_audit_action`/`enqueue_audit_action` bus payload has no correlation slot and is not extended** (a
transparency/mutation seam cannot grow a 12th field without breaking the frozen vocab §③.2). This resolves
`06 §12`'s open co-decision **not** by its option (a) (a 12th bus field) or (b) (encoding into
target/scope) but by **homing correlation on the DB spine K7 already owns** — no frozen seam is touched.
Whether the **live** bus event *also* needs correlation (to group draft-apply rows in real time in
`server_logging`) is a bounded owner-gated retention question tied to SF-c (§9 deferral 6 / open decision).

**Dedup key = `mutation_id` PK**: exactly-once is enforced upstream by `once()` (the guard row), so the
insert is never contended; the PK is the belt-and-braces. Domain ledger tables (e.g.
`economy_audit_log`) remain, written by their DB legs as the domain money trail — `audit_log` is the
generic spine row, not their replacement. **Migration:** `000N_audit_spine.sql` creates `audit_log`
in the K7 band.

---

## 6. Restart & merge=deploy behavior (exactly-once)

The engine is **stateless**; all durability is K3 (`idempotency_keys`) + `audit_log` + the outbox
(`event_outbox`). It arms **no timers** — invocation is synchronous from dispatch, so K7 needs **no
boot-reconcile** (that is the scheduler K-fn's job; K7 only supplies the `once()`+`db.transaction()`
substrate the scheduler's boot-reconcile fires *through* via `run_ref(conn=…)`).

- **Dual-instance overlap (L-6, the fast-release window).** A MESSAGE_CREATE/interaction delivered to
  both gateway connections invokes `run()` twice. For `DURABLE_ONCE`, both open `db.transaction()`; the
  second `once(key,conn)` sees the guard row (row-locked until the first commits) → `read_outcome` →
  `_reproduce` the first `WorkflowResult` with **zero re-effect** (§3.7). **farm-collect stops
  double-crediting.**
  - **The dedup token MUST encode the actor (the cross-user-safety fix).** `IdempotencyKey` carries no
    `user_id` (vocab §④.1: `{namespace, guild_id, dedup_token}`), so a bare "coop pre-collect timestamp"
    token is a **cross-user fund-loss bug** — two different users collecting in the same guild at the same
    integer-second would collide on one key and the second user would be deduped as a replay of the first
    (uncredited). The natural key for the L-6 double-gateway delivery is the **triggering event id**
    (K3's own guidance, §④.1: `dedup_token = message_id | interaction_id | …`), which is per-user-unique.
    So farm-collect declares:
    ```python
    dedup_key = DedupKeySpec(source=("user_id", "interaction_id"))
    # render(ctx) -> f'{ctx.params["user_id"]}:{ctx.params["interaction_id"]}'
    ```
    The **same** interaction delivered to both gateways shares `(user_id, interaction_id)` → one key →
    correct dedup. **Two different users** → different `user_id` → different keys → both credited. A
    legitimate later collect by the same user → a new `interaction_id` → a new key → allowed. (For a
    prefix-command faucet with no interaction id, the token is `f'{user_id}:{message_id}'` — same
    per-user-unique shape.)
  - `NATURAL_KEY` ops (escrow: `FOR UPDATE` row-consumption, `game_wager_workflow.py:26-28`) are already
    once by construction — no guard row, no dedup token.
- **merge=deploy restart mid-op.** An op interrupted before commit rolls back atomically (nothing
  persisted, no `record_outcome`) — the actor re-invokes and it runs clean. An op interrupted *after*
  commit but before EFFECT legs leaves DB state correct + audit row written + the durable
  `audit.action_recorded` outbox row captured (so the central trace redelivers on boot); a missed
  `BEST_EFFORT` EFFECT (a Discord notice) is a best-effort loss, while an `AT_LEAST_ONCE` emit is
  redelivered by the outbox relay on boot (owned by the outbox sibling). This matches the shipped "emit
  after commit" honesty (`farm_workflow.py:158`, `game_wager_workflow.py:39`) with a durable upgrade path.
- **Invariant honored:** effects are dedup-guarded by `once()`+`db.transaction()` **uniformly** across
  prefix/interaction/non-message lanes (why fast-release is *correct* where the `#1693` listener-only
  gate was not — vocab §⑤.1).

---

## 7. Architecture rules honored (INV / layer cites)

- **Layer.** Engine in `sb/kernel/workflow/` (kernel) imports `utils`, `sb/spec/*`, `sb/kernel/db/*`,
  `sb/kernel/outbox/*`, `kernel/authority/*` — **never `cogs/` or `views/`** (services→views
  zero-tolerance honored; `CLAUDE.md` layer table). Leg handlers live in `domain/<x>/` and are reachable
  only via registered `WorkflowRef`s.
- **All DB via `utils.db.*`.** Leg handlers receive `conn` and call `utils.db.*` conn-aware primitives
  **only** — this **retires** the shipped raw-`conn.execute` in `economy_service.transfer` (`:253`,
  a `utils/db`-boundary violation) by re-homing it as a DB leg. The `atomic_db_only` fence (§3.6) makes
  this AST-enforced for every external-conn DB leg.
- **All mutations through the domain `*_mutation.py` seam.** DB legs call the domain mutation service;
  the engine is the *composition* layer above them.
- **All auditable mutations call the audit seam.** Guaranteed centrally **once** per op (the `audit_log`
  row + the durable `enqueue_audit_action` bus trace, §3.4), and enforced at compile by the
  `audit_completeness` fence: a spec with `effect="mutating"` MUST carry a `WorkflowRef` (= a
  `CompoundOpSpec`) or it is a `SEMANTIC_VIOLATION` → CI-red (vocab §③.4).
- **Settings via `settings_keys` constants** — leg handlers touching settings use the constants, never
  raw keys.
- **INV-F** (economy audited-money boundary): escrow/settle ops are `CompoundOpSpec`s (the
  `game_wager_workflow` family), keeping every coin movement inside one audited txn.
- **Complexity budget (§1.5):** the engine removes the defer/auth/mutate/audit choreography from every
  callback — per-op code is a declaration + small leg handlers, so no `process()`-class god-function
  can accrete (each leg ≤ 15 cognitive / ≤ 80 lines by construction).

---

## 8. Options → Decision → Why (per fork closed)

| Fork | Options | **Decision** | Why |
|---|---|---|---|
| **A · T2-1 "atomic" + engine entry** | (i) single self-txn `run(spec)` only (ii) drop "atomic" entirely (iii) `LegKind.DB`/`EFFECT` split **+ an external-conn seam** (`run_ref(conn)`/`apply(op,conn)`) so a caller-owned txn can carry the pure-DB leg set | **(iii)** — DB/EFFECT split; "all-or-nothing" reserved for the DB-leg set; **the external-conn entries let the scheduler (`09:389`) and the invariant/version repair-compensation callers (`09:228`) run legs in *their* txn under *their* `once()`; the draft runs each op through `run()` per-op** (`06 §3.5`, own txn per op) | A#1 verbatim ("reserve all-or-nothing for pure-DB compound ops"); Discord ops can't roll back — encode it structurally. **The single-entry `run(spec)` was structurally incompatible with the scheduler's external `conn`**; the external-conn seam (`run_ref`) is the co-decision. **F-2 resolves by caller type (PIN-2): the draft's EFFECT-bearing resource-create ops go through `run()` per-op (per-op-atomic + idempotent-resume, NOT one shared txn); only pure-DB scheduler/invariant/version callers use `run_ref`/`apply`.** |
| **B · audit granularity (③.3) + correlation** | (i) N rows, one per leg (ii) one row per op (iii) one row + a correlation id on the DB spine for the draft-apply group | **(ii)+(iii): one central row per invocation, legs = sub-detail; N rows ONLY when ④ invokes N ops, correlated by `audit_log.correlation_id` (a DB-spine column, NOT a 12th bus field)** | §③.3 "batched lifecycle op ⇒ 1 row"; keeps one-op = one-`mutation_id`. Homing correlation on the spine (§5) resolves `06 §12` without touching the frozen 11-field bus payload. Live-bus correlation is SF-c (deferred). |
| **C · T2-21 idempotency** | (i) implicit single-flight (ii) mandatory declared posture (iii) per-leg keys | **(ii) `IdempotencyPosture` required + `idempotency_posture_declared` fence**, with the posture's mandated companion field (`dedup_key` / `idempotency_justification` / `single_flight_scope`) enforced | T2-21 mandate ("mandate a declared posture; single-flight is an *allowed* posture"). Closes L-6 for the workflow lane; a mutating op with no posture (or a posture missing its mandated field) is CI-red. |
| **D · dry-run mechanism** | (i) handler-declared preview mode (ii) txn-rollback + skip-effects (iii) dual codepath | **(ii) txn-rollback + skip EFFECT/best-effort legs (structural); handler `ctx.dry_run` is an optional optimization** | `automation_executor` precedent generalized; the rollback is a *guarantee*, not per-handler discipline (the L-16/oracle "structural not exhortation" lesson). |
| **E · EFFECT-leg failure post-commit** | (i) saga/compensation engine (ii) compensator-if-declared else record-finding (iii) blind retry | **(ii) run `compensator` if declared (COMPENSATABLE), else record an operator finding → PARTIAL** | A#26 blessed "record left-behind side-effects without a saga engine" as a Tier-3 default; no saga engine in v1. |
| **F · outbox coupling (L-9) + `DeliveryClass` home** | (i) engine owns delivery + its own `DeliveryClass` (ii) engine writes outbox row in-txn via the sibling, **importing the sibling's `DeliveryClass`** (iii) best-effort only | **(ii) `outbox.enqueue_all(…, conn=conn)` in-txn + `enqueue_audit_action` for the central trace; `DeliveryClass` imported from `sb/spec/events.py` (canonical home, §12 #1)** | Delivery is the outbox K-fn's (L-9/T2-3), not K7's; the central audit event becomes crash-durable. One `DeliveryClass` enum shared with `EventSpec.delivery` — no drift (the RC-3 Lane lesson). |
| **G · error return** | (i) `run()` raises classified failures (ii) `run()` catches, rolls back, RETURNS a classified `WorkflowResult`; reserve the resolver's "exceptions" path for unexpected escapes | **(ii)** | The draft's per-op loop (`06:316`) needs a *returned* per-op result to continue and aggregate to PARTIAL; the resolver classifies only genuine escapes. Returning keeps both consumers consistent (§3.3-note). |
| **H · confirm gate condition** | (i) engine gates on `reversibility==IRREVERSIBLE` (ii) engine gates on `confirmation is not None` (presence), matching the resolver + design §2.7 | **(ii) presence** | A confirm-bearing *reversible* op (FJ T2-5: confirm = destructive ∨ AI-produced ∨ bulk/compound) invoked via a non-resolver path must not bypass the backstop; `ConfirmRequired` is a control signal, and `atomic_db_only` forbids a confirm-bearing external-conn spec (§3.6). |

---

## 9. Labeled deferrals (each bounded)

1. **Per-plan orchestration failure policy (SF-f).** v1 = required-leg-abort / optional-leg-degrade /
   stop-on-first-non-SUCCESS. A per-plan continue/compensate policy is Phase-4 band-6 (bounded; the
   `optional` flag + compensator seam already carry the default).
2. **Durable compensation / saga engine.** Deferred (A#26); v1 records findings. The `compensator`
   `WorkflowRef` field is the forward seam.
3. **Durable outbox delivery (L-9/T2-3).** Owned by the outbox K-fn; K7 provides the in-txn write
   point (`enqueue_all`/`enqueue_audit_action`) + consumes `DeliveryClass`. Bounded by that sibling's spec.
4. **`ChallengeSessionSpec.refund_policy` wiring.** The engine composes it as an EFFECT/compensator
   leg; the game-facet band (Phase 4 §9.2 step 5) authors the concrete handler.
5. **Cooldown durability (SF-e).** Not K7 — the resolver reads `CooldownSpec` at step 3; the engine
   never sees cooldown.
6. **Live-bus correlation for draft-apply grouping (SF-c-adjacent).** The DB spine already carries
   `correlation_id` (§5), so the operator *forensic* log groups draft-apply rows today. Whether the
   **live** `audit.action_recorded` bus event *also* needs correlation (to group N rows in real time in
   `server_logging`) is owner-gated retention (tied to SF-c dispatch-trace promotion) — surfaced as an
   open decision, not a blocker; v1 default = DB-spine only (the frozen 11-field bus payload untouched).
7. **`AT_LEAST_ONCE` membership for `audit.action_recorded` (08 §open).** The *mechanism* (durable
   `enqueue_audit_action`) is fully built; *whether* the central audit event is `AT_LEAST_ONCE` (durable,
   recommended) vs `BEST_EFFORT` (shipped honesty) is owner-gated per `08` — surfaced as an open decision;
   v1 default = `AT_LEAST_ONCE`.

All deferrals sit behind a designed seam; none blocks building the engine + the canary now.

---

## 10. Retirement map

| Row (FJ §2 L / §4 gap / §6 owner-queue) | How this spec retires it |
|---|---|
| **K7 — the ~48-multi-leg-txn-site concern** | The `LegSpec`/`CompoundOpSpec`/`run()`/`run_ref()`/`apply()` engine replaces the multi-leg `db.transaction()` sites (of the ~66 total per-file sites, ~48 multi-leg) with declarations + leg handlers; §2 maps each file. **CLAIMED / CLOSED.** |
| **the engine-entry seam (cross-sibling)** | Three co-designed entries over one core (`run` self-txn — the resolver target **and the draft's per-op entry** / `run_ref(conn)` scheduler + invariant + version / `apply(op,conn)` the op-kind external-conn sibling) + `WorkflowRegistry` for `WorkflowRef`/`op_kind`→`CompoundOpSpec`; matches `02:218`, `06:451-466`, `09:389,491` exactly (§3.2). **CLOSED — the single-entry mismatch resolved; F-2 (PIN-2) resolved by caller type.** |
| **T2-1 — atomic-apply meaning (owner-queue A#1)** | `LegKind.DB`/`EFFECT` split + the external-conn seam ⇒ a caller-owned txn carries the pure-DB leg set for the scheduler / invariant-repair / version-compensation callers (§8 fork A). **The draft (F-2, PIN-2) does NOT share one txn across N ops — it runs each op through `run()` per-op (per-op-atomic + idempotent-resume), because its resource-create ops bear post-commit EFFECT legs. CLOSED by caller type.** (The word "atomic" for the *resource-create* lane stays ④'s owner-gated fork, not K7's.) |
| **T2-21 — idempotency posture mandate per mutating action (A#13)** | `IdempotencyPosture` required field + compiler fence + mandated companion fields; 4 postures incl. single-flight (§8 fork C). **CLAIMED / CLOSED.** |
| **③.3 audit-row-granularity fork (inherited from ④)** | One central `audit_log` row per compound-op invocation; N rows only from ④'s N invocations, correlated by the DB-spine `correlation_id` (§3.4, §5, §8 fork B). **CLAIMED / COMPLETED.** |
| **L-9 — no outbox / commit-then-emit outside txn (incl. the CENTRAL audit trace)** | Engine writes `AT_LEAST_ONCE` emits **and** the central `audit.action_recorded` trace as outbox rows **inside** the txn via `enqueue_all`/`enqueue_audit_action` (§3.4, §8 fork F). **CONSUMED (seam provided); the central-trace crash-loss gap closed here, delivery retired by the outbox K-fn.** |
| **L-6 — deploy-overlap double-fire (workflow lane share)** | `DURABLE_ONCE` + `once()`+`db.transaction()` makes every mutating op exactly-once across the fast-release window; farm-collect's **actor-encoded** dedup token (`user_id:interaction_id`) stops double-crediting **and** cross-user collision (§6). **PARTIALLY CLOSED (workflow lane; prefix/interaction lanes co-owned with the resolver dedup checkpoint).** |
| **FJ §4 item 15 — named canaries have no failure arm** | `preview()`'s oracle defines farm-collect's pass/fail: **preview diff matches expected + dry-run leaves DB byte-identical + zero effect calls** = the canary's failure arm (§3.5). **PARTIALLY CLOSED (farm-collect; mining-last canary follows the same oracle).** |
| **L-8 (audit-only, money legs) — farm-collect audits only the coin leg** | The central row captures all 3 legs (credit + coop-reset + XP) with full before/after; the coop-reset/XP audit gap closes. **CLOSED for the canary; the pattern generalizes.** |

---

## 11. Build order (K0-K10 placement + what it blocks)

**Placement:** **K7 — "the workflow engine … the largest kernel band"** (design §9.1:1609), **after
K6 (authority)**, **before K8 (interaction runtime)**. Depends only on layers above it (K1 namespace,
K2 grammar/refs + `sb/spec/events.py`'s `DeliveryClass` + `sb/spec/confirmation.py`, K3 db+idempotency,
K4 events/outbox, K5 lifecycle, K6 authority).

**Sub-order within K7 (each lands with its checker):**
1. `result.py` — adopt `WorkflowResult`/`MutationPreview`/`StepResult` + the `from_*` adapters + the
   `ConfirmationSpec` re-export (design §2.7; test-pinned against recorded legacy audit rows).
2. `spec.py` + `context.py` + `registry.py` — `LegSpec`/`CompoundOpSpec`/`IdempotencyPosture`/
   `WorkflowContext`/`WorkflowRegistry` + `compile.py` fences (`idempotency_posture_declared`,
   `audit_completeness`, `atomic_db_only`).
3. `audit.py` — `audit_log` migration + `emit_central_audit` over `enqueue_audit_action` + the audit DB leg.
4. `engine.py` — `run()`/`run_ref()`/`apply()`/`preview()` over one `_execute` core, on K3
   `once()`/`db.transaction()` + the outbox `enqueue_all`.
5. **canary:** port `economy.farm.collect` (actor-encoded `dedup_key`) + write the dry-run oracle test
   (the Gate-V acceptance).

**What K7 blocks (nothing downstream builds without it):**
- **K8** — `resolve()` step 5 `INVOKE_WORKFLOW` calls `run()`, returns `WorkflowResult`; `Result.workflow`
  wraps it.
- **The scheduler ⑤** — `_fire` calls `run_ref(timer.handler, ctx, conn=conn)` (09:389).
- **The draft pipeline ④** — `apply_draft` resolves each `DraftOperation` → `CompoundOpSpec` and calls `run(spec, ctx)` **per-op** (own txn per op; NOT `apply`/one shared txn — F-2, PIN-2; 06 §3.5).
- **The game facet (design §2.8)** — `ChallengeSessionSpec.escrow` + `IdleAccrualSpec.collect_workflow`
  are `CompoundOpSpec`s.
- **All Phase-4 mutating ports (§9.2)** — every `*_mutation` routes through a `CompoundOpSpec`; the
  `audit_completeness` fence makes it non-optional.

---

## Seam corrections (flagged; source-wins Q-0120)

1. **Engine entry — the single-entry `run(spec, ctx)` mismatched the external-conn consumers (now co-designed).**
   The earlier draft advertised one entry `run(spec: CompoundOpSpec, ctx)` that opened its own
   `db.transaction()` + `once()`. But the scheduler calls `engine.run_ref(ref, ctx, *, conn)` with a
   `WorkflowRef` + external conn (`09-scheduler-state.md:389,491` — legs run in the scheduler's own txn +
   `once()`), and the invariant/version repair-compensation path calls `run_ref(compensation_ref, ctx,
   conn=conn)` on its own txn (`09:228`); the resolver dispatches a `WorkflowRef` (`02:218`,
   `INVOKE_WORKFLOW`) needing a `WorkflowRef→CompoundOpSpec` resolution; the **draft** resolves each
   `DraftOperation` → `CompoundOpSpec` and calls `run(spec, ctx)` **per op** (`06-draft-pipeline.md:451-466`
   — own txn per op, because its resource-create ops bear post-commit EFFECT legs the `atomic_db_only`
   fence excludes from the external-conn path). A self-owned-txn-only `run(spec)` is **structurally
   impossible** for the external-conn callers (their `conn` has no way in; a re-acquired connection would
   break guard-row/effect atomicity + double-`once()`).
   **Correction:** three entries over one core — `run()` (self-txn, the resolver target **and the draft's
   per-op entry**), `run_ref(conn=…)` (the scheduler / invariant / version external-conn fire), `apply(op,
   conn)` (the op-kind external-conn **sibling** of `run_ref`, declared per 06) — plus `WorkflowRegistry`
   for the ref/op_kind→spec resolution (§3.2). **F-2 (PIN-2) resolves by caller type:** EFFECT-bearing draft
   ops → `run()` per-op (per-op-atomic + idempotent-resume, NOT one shared txn); pure-DB
   scheduler/invariant/version callers → `run_ref`/`apply` — not asserted-closed over a hole.
2. **`DeliveryClass` canonical home is the outbox leaf (absorbs `08 §12` seam-correction #1).** The
   earlier draft **defined** `class DeliveryClass` locally in `sb/kernel/workflow/spec.py`. The outbox
   sibling moved the canonical home to `sb/spec/events.py` (alongside `EventSpec.delivery`) so
   `EventEmitSpec.delivery` and `EventSpec.delivery` share **one** enum (the RC-3 Lane-drift lesson).
   **Correction:** K7 **imports** `DeliveryClass`; it does not define it (§2, §3.1). Two enums retired to one.
3. **The central audit BUS trace was best-effort-lossy (now durable).** The earlier draft routed the
   compound-op `audit.action_recorded` trace through best-effort `emit_audit_action` (returns `False` on
   loss). That leaves the very L-9 gap the outbox sibling exists to close for the central event. The
   sibling built the **durable twin `enqueue_audit_action(conn, …)`** (`08:150`, §12 #2) — an in-txn
   writer carrying the identical 11-field payload, delivering the identical event. **Correction:** K7's
   central audit (§3.4) writes the trace via `enqueue_audit_action` in-txn (recommended
   `AT_LEAST_ONCE`), with `emit_audit_action` as the `BEST_EFFORT` fallback. `emit_audit_action` itself is
   **never edited** (the frozen 11-field seam, vocab §③.2).
4. **`correlation_id` has a DB path, not a bus path (resolves `06 §12`).** The frozen 11-field bus payload
   has no correlation slot and cannot grow one. **Correction:** `WorkflowContext.correlation_id` (set by ④
   = `draft_id`) is written into the `audit_log.correlation_id` **DB column** by the central audit leg
   (§5); the bus payload stays 11 fields. Neither `06`'s option (a) (12th field) nor (b) (encode into
   target/scope) — the spine column K7 owns.
5. **The `dedup_token` for a per-user faucet must encode the actor.** `IdempotencyKey` carries no
   `user_id`; a bare timestamp token collides across users in a guild → the second user is deduped as a
   replay and uncredited (cross-user fund loss). **Correction:** farm-collect's `dedup_key` is
   `DedupKeySpec(source=("user_id", "interaction_id"))` (per-user-unique; K3's own event-id guidance);
   never a bare timestamp (§6).
6. **Design-spec §2.8 `ChallengeSessionSpec.escrow` "routes through the economy engine's
   `bet_and_settle` seam (INV-F)" is imprecise.** Verified: `economy_service.bet_and_settle`
   (`:289-327`) is a **single-wallet, non-transactional** primitive (no `db.transaction()`; one
   `db.add_coins` + one audit). Two-party **escrow** is `game_wager_workflow.open_pvp_wager`/
   `settle_pvp`/`refund_pvp` (`:89-…`), which composes `debit_in_txn`/`credit_in_txn` **inside one
   `db.transaction()`** with `FOR UPDATE` row-consumption idempotency (`:26-28`). **Correction:**
   escrow routes through a `CompoundOpSpec` porting the `game_wager_workflow` family;
   `bet_and_settle` is the **single-party settle leg handler**, not the escrow workflow. Both are
   leg-level primitives the engine composes.
7. **`economy_service.transfer` (`:253`) uses raw `conn.execute`** — a `utils.db`-boundary violation
   the shipped code carries. K7's leg discipline (handlers call `utils.db.*` only, AST-enforced by
   `atomic_db_only`) retires it as a DB leg; not a divergence, a cleanup the engine forces.
```
