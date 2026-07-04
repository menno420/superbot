# Strand-2 · ⑦ The durable scheduler / due-queue + versioned-state policy (K-fn) — Buildable Design Spec

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B design contract. Precedence: shipped source &
> merged PRs > the five strand-1 specs (for shapes they own) > the frozen `shared-vocabulary.md` >
> this doc. This doc **builds on** the frozen vocab (`../shared-vocabulary.md` §①–⑩) and **completes**
> the one skeleton it explicitly left for the scheduler: **§⑤.5 "the scheduler completes the
> restart-safety pattern"** — the durable-timer table shape + the boot-reconcile-fires-overdue-
> exactly-once procedure. It also owns the two undesigned durability fields the design-spec §2.8
> grammar leaves empty (`ManagedTaskSpec` durability/misfire/catch-up; `StoreSpec` payload-version
> policy). Spot-verified against shipped source this session (cites inline). Design against frozen
> decisions Q-0219…Q-0237 (incl. Q-0237a-g) — never re-decided here.
>
> **Consumes the FROZEN shared vocabulary:** the error envelope ①, `resolve_authority` scripted-bypass
> ②, the audit-row semantics ③, the idempotency-key contract ④, the restart-safety pattern ⑤. And the
> three written strand-2 siblings, **reconciled against their shipped shapes this revision (source-wins,
> Q-0120):** K7 workflow engine (`07-workflow-engine.md` — `run()`/`run_ref(ref, ctx, *, conn)`/`apply()`/
> `IdempotencyPosture`/the `atomic_db_only` fence), K9 draft pipeline (`06-draft-pipeline.md` — the
> `select_expired` janitor it hands me), and **the outbox relay (⑥, `08-event-outbox.md` — now WRITTEN)**,
> which owns its own supervised `RELAY_TASK` loop; I neither host nor boot-reconcile it (§4/§11).

---

## 1. Summary + the exact undesigned gap

**What ⑦ is.** One always-on kernel poll loop with a **durable due-queue** (persisted armed timers),
a **claim/lease** that is dual-instance-safe, and a **boot-reconcile** that fires every overdue timer
**exactly once**. Plus the **payload-version policy** primitive (`{upcast, reject_and_preserve, drop}`)
that decides, at load time, whether a persisted payload whose schema version drifted across a deploy
is upcast-and-resumed, compensated-then-retired (refund-before-delete), or dropped — declared once on
`StoreSpec`, enforced by one kernel function, replacing the per-cog hand-written recovery branch that
still forfeits real money (L-1).

**Already designed (anti-pad — I do not re-derive these):**
- **Design-spec §2.8 `ManagedTaskSpec`** already declares `name` / `trigger: Interval|Cron|Event` /
  `handler: HandlerRef` / `error_policy` / `metrics_labels`. It has **no persistence / misfire /
  catch-up field** — that empty half is my gap (T2-6).
- **Design-spec §2.8 `StoreSpec`** already declares `table` / `sole_writer` / `retention` /
  `checkpoint_class: {ledger, aggregate, session}` / `invariant_tag` / `reader_domains`. It has **no
  payload-version-mismatch policy field** — that empty half is my gap (T2-7).
- **K3 idempotency** (`once`/`record_outcome`/`read_outcome` + `idempotency_keys` + `db.transaction()`)
  is owned by spec 05 (vocab §④). I **consume**, never redefine, it.
- **K7's fire entry `run_ref(ref, ctx, *, conn) -> WorkflowResult`** + `IdempotencyPosture` + the
  `atomic_db_only` fence are owned by `07-workflow-engine.md` (§3.2/§3.6). A ManagedTask's fire routes
  through `run_ref` on **my** conn; I **consume** it as the fire target (§4).
- The **draft `select_expired` sweep** is owned by `06-draft-pipeline.md` §3.3/§6; it "rides the
  scheduler's janitor lane" — I **host** it as a registered `PollLane`, I do not re-implement it.
- The **outbox relay** (`08-event-outbox.md`) is owned by ⑥ as its **own** supervised `RELAY_TASK`
  `ManagedTaskSpec(Interval 1s)` (08 §3.4). I do **not** host or reconcile it — it is a peer supervised
  task on the same K5 host, self-reconciling (08 §8 fork E). I only supply the `ManagedTaskSpec`
  *durability grammar* it (and every other declared task) is written in.

**The genuinely undesigned gap this spec closes (all ⑦-owned):**

| Undesigned today | What this spec delivers | Evidence (shipped, verified) |
|---|---|---|
| The only durable poller **defaults OFF and its spawn is inert** | one **always-on** kernel `PollSupervisor` (no enablement flag; kernel restart-safety cannot be opt-in) | `automation_scheduler.py:388-397` — `AUTOMATION_SCHEDULER_ENABLED` defaults `"false"`, `spawn_scheduler` returns `None` |
| Its claim "so two concurrent schedulers cannot double-run" is **defeated cross-instance** | a deterministic `dedup_token = f"{task_id}:{fire_epoch}"` + `FOR UPDATE SKIP LOCKED` lease + the §④ `once()` belt-and-braces | `_idempotency_key` appends `uuid.uuid4()` (`automation_scheduler.py:263-275`) → both instances' `claim_run` INSERT succeed under the same tick → **double-fire**; the docstring's :11-13 claim is false for the merge=deploy overlap |
| One-shot timers are **in-memory `asyncio.sleep`, lost every deploy** | a `OneShot` trigger kind persisted in the due-queue; boot-reconcile re-fires overdue one-shots | `blackjack_cog.py:410` (reaction-join window), `:572` (`sleep(duration_mins*60)` tournament countdown), `rps_tournament/_helpers.py:126,192` (`sleep(300)`) |
| No boot-reconcile ordered against `/ready`; no misfire/catch-up semantics | `reconcile_on_boot` fires overdue timers under `once()` **after lifecycle RUNNING**, applying a declared `MisfirePolicy` | `automation_scheduler` re-arms nothing at boot; recovery paths re-arm zero timers (L-8) |
| `game_state_service.save()` has a `version` column but **delegates drop-vs-resume to cogs — no upcast primitive** | `resolve_versioned_load(store_spec, row)` — the one load-time primitive; `version_policy` declared on `StoreSpec` | `game_state_service.py:68-72` docstring: "an adopting cog should compare … and decide whether to resume the game or refund + clear" |
| **THE RPS FORFEIT IS STILL LIVE** — version-mismatch rows cleared without refund | `version_policy = REJECT_AND_PRESERVE` **generates** refund-before-delete; the hand-written recovery branch is retired; DROP on a value-bearing store is a compile violation | `rps_tournament/_persistence.py:104-115` — `clear_by_id` + `continue`, skipping the refund block; the guild-remove path (`:251-270`) refunds, proving the pattern is known |

**Named canary:** `rps_tournament` recovery on an `RPS_TOURNAMENT_VERSION` bump. Today (V-1, a separate
immediate PR) it forfeits the entry fee; under this design the `StoreSpec.version_policy =
REJECT_AND_PRESERVE` recovery **refunds before any delete**, idempotently. The dry-run oracle: bump the
version, run boot-reconcile, assert the fee is refunded exactly once and no row is force-deleted before
the refund commits. This is the **durable class fix** V-1 is the stopgap for.

---

## 2. Files / modules it becomes

**New `sb/` paths** (kernel layer — imports `sb/spec/*`, `sb/kernel/db/*`, `sb/kernel/authority/*` K6,
the K7 workflow-engine port, the K5 lifecycle port; **never** views/cogs):

| Path | Owns |
|---|---|
| `sb/spec/scheduler.py` | leaf: `TaskDurability`, `MisfirePolicy`, `TriggerKind`, `TaskScope`, `ErrorPolicy` enums; `Interval`/`Cron`/`OneShot`/`EventTrigger`; the **durability-extended `ManagedTaskSpec`**. Imports **no** kernel module (leaf — the `IdempotencyPosture` inversion is retired, §12 #2). |
| `sb/spec/versioning.py` | leaf: `VersionPolicy`, `CheckpointClass` enums; `VersionedRow`; the **version-extended `StoreSpec`** (adds `payload_version` / `bears_value` / `version_policy` / `active_rows_ref` / `retire_ref` / `upcast_ref` / `compensation_ref`) |
| `sb/kernel/db/scheduler.py` | DB primitive (asyncpg only): `sb_due_queue` CRUD — `arm` / `claim_due` (SKIP LOCKED) / `mark_fired` / `mark_failed` / `mark_dead` / `reap_expired_leases` / `select_overdue` (read-only diagnostic) / `cancel` / `cancel_scope` |
| `sb/kernel/scheduler/poll.py` | `PollSupervisor` (one supervised loop) + `PollLane` port + `LaneTickResult`; the shared poll host the **due-queue lane + the draft janitor lane** register on (the outbox relay is a *peer* supervised task, not a lane here — §4/§11) |
| `sb/kernel/scheduler/due_queue.py` | `DueQueueLane` (a `PollLane`): `tick` (claim→fire) + `reconcile_on_boot` (reap→claim-loop→misfire→fire) + `arm_declared_tasks` (first-boot arming); `_fire` (the `once()`-guarded fire); `arm_task`/`arm_one_shot`/`cancel_task`; the `SYSTEM_ACTOR` fire sentinel |
| `sb/kernel/scheduler/misfire.py` | `apply_misfire(timer, now) -> MisfireDecision` — pure; the coalesce/fire_all/skip decision + the recurring next-slot advance |
| `sb/kernel/versioning/resolve.py` | `resolve_versioned_load(spec, row, …) -> LoadDisposition` — the load-time upcast/compensate/drop/quarantine primitive; `run_recovery(store_spec, …)` — the generated recovery sweep replacing per-cog branches |
| `sb/kernel/versioning/compile.py` | the `version_policy_declared` compiler fence (value-bearing session/ledger store MUST declare a non-DROP policy + its mandated companion ref) |

**Retired shipped paths** (§10 maps each to an L-row):

| Retired | Replaced by |
|---|---|
| `disbot/services/automation_scheduler.py` (bespoke poll loop, `_fetch_due_rules` raw `pool.fetch`, uuid-defeated claim, OFF-by-default spawn) | `sb/kernel/scheduler/poll.py` (`PollSupervisor`) + `DueQueueLane`; the automation *feature* becomes a **producer** of durable timers + a fire-handler, not its own scheduler |
| `disbot/utils/db/automation.py::claim_run` / `_idempotency_key` (uuid-random dedup) | `sb/kernel/db/scheduler.py::claim_due` (SKIP LOCKED lease) + deterministic `dedup_token` + K3 `once()` |
| `blackjack_cog.py:410,572` / `rps_tournament/_helpers.py:126,192` (in-memory `asyncio.sleep` one-shots) | `arm_one_shot(ManagedTaskSpec, fire_at)` — durable `OneShot` timers, boot-reconciled |
| `rps_tournament/_persistence.py::recover_rps_tournament` + `blackjack_cog._recover_blackjack_*` (hand-written drop-vs-refund branches) | `run_recovery(store_spec)` **generated** from `StoreSpec.version_policy` (`resolve_versioned_load` per row) |
| `game_state_service.py` load-side "cog decides resume/refund+clear" delegation | `resolve_versioned_load` — one kernel primitive; the cog declares a `StoreSpec`, writes no branch |

The automation domain feature, RPS/blackjack recovery, and the game_state GC (`game_state_cleanup.py`)
all become **thin declarations** (a `ManagedTaskSpec` + a `StoreSpec`) over these kernel primitives —
none re-implements a poll loop, a claim, or a drop-vs-refund branch.

---

## 3. The complete public contract

Tags: **[S]** manifest/spec field · **[O]** objective input · fields with no tag are durable runtime
state (DB rows) or derived.

### 3.1 `sb/spec/scheduler.py` — the durability-extended `ManagedTaskSpec`

```python
class TaskDurability(StrEnum):
    IN_MEMORY = "in_memory"   # supervised task only; lost on restart (shipped default) — pure-cache/best-effort
    DURABLE   = "durable"     # persisted in sb_due_queue; survives merge=deploy; boot-reconciled

class MisfirePolicy(StrEnum):              # governs RECURRING timers only (a one-shot always fires once — §3.7)
    COALESCE = "coalesce"     # N missed fires while down -> ONE fire on boot (A#7 default; accrual-safe)
    FIRE_ALL = "fire_all"     # replay every missed interval, bounded by max_catchup (rare; count-exact tasks)
    SKIP     = "skip"         # drop all missed fires; re-arm forward only ("latest snapshot" tasks)

class TriggerKind(StrEnum):
    INTERVAL="interval"; CRON="cron"; ONE_SHOT="one_shot"; EVENT="event"

class TaskScope(StrEnum):
    GLOBAL="global"; GUILD="guild"    # GUILD tasks are reclaimed on guild-leave (C-8 / T2-8)

class ErrorPolicy(StrEnum):           # design §2.8 verbatim
    LOG="log"; DISABLE_AFTER_N="disable_after_n"; ESCALATE_FINDING="escalate_finding"

@dataclass(frozen=True)
class Interval: seconds: int          # [S] persisted on the timer as interval_seconds (drives _next_fire_at)
@dataclass(frozen=True)
class Cron:     expr: str             # [S] 5-field; parser = a bounded impl detail (§9); persisted as cron_expr
@dataclass(frozen=True)
class OneShot:  pass                  # fire_at is a runtime arm-time arg, not [S]
@dataclass(frozen=True)
class EventTrigger: event: str        # [S] bus event name — armed by the bus, NOT polled (out of the due-queue)

@dataclass(frozen=True)
class ManagedTaskSpec:                 # EXTENDS design-spec §2.8 — the base 5 fields are unchanged
    name: str                          # [S] "<subsystem>:<purpose>" — namespace kind task_prefix (design §2.8)
    trigger: Interval | Cron | OneShot | EventTrigger   # [S] (design §2.8 + OneShot added — retires asyncio.sleep)
    handler: WorkflowRef | HandlerRef  # [S] the fire target; MUST be a WorkflowRef if the fire mutates (fence §3.4/③.4)
    error_policy: ErrorPolicy          # [S] (design §2.8)
    metrics_labels: tuple[str, ...] = ()   # [S] (design §2.8)
    # ---- NEW durability fields (the undesigned gap — T2-6) ----
    durability: TaskDurability = TaskDurability.IN_MEMORY   # [S] DURABLE ⇒ persisted + boot-reconciled
    misfire_policy: MisfirePolicy = MisfirePolicy.COALESCE  # [S] (A#7 default) — recurring only
    catch_up: bool = True              # [S] recurring: True ⇒ boot-reconcile fires overdue; False ⇒ re-arm forward, never back-fire
    grace_s: int = 0                   # [S] a fire this-many-s late is still "on time"; beyond it MisfirePolicy applies
    scope: TaskScope = TaskScope.GLOBAL   # [S]
    max_catchup: int = 1               # [S] FIRE_ALL cap — max missed fires replayed on boot (thundering-herd guard)
```

**No `idempotency` field (the layering-inversion fix — §12 #2).** The earlier draft carried
`idempotency: IdempotencyPosture` here, but `IdempotencyPosture` is homed in the **kernel** module
`sb/kernel/workflow/spec.py` (07 §2), so a `sb/spec/` leaf referencing it is an upward/circular import —
the exact fault 08 §12/RC-3 fixed for `DeliveryClass`. The field is also **redundant**: every durable
fire is unconditionally guarded by the scheduler's **deterministic `once()`** (`dedup_token =
task_id:fire_epoch`, §3.7) — the fire is durable-once *by construction*, with no per-task variation. The
*fired workflow's* own posture is declared on its `CompoundOpSpec` (07). So the field is dropped, and the
leaf imports nothing from the kernel (§12 #2).

### 3.2 `sb/spec/versioning.py` — the version-extended `StoreSpec`

```python
class CheckpointClass(StrEnum):        # design §5.1 verbatim
    LEDGER="ledger"; AGGREGATE="aggregate"; SESSION="session"

class VersionPolicy(StrEnum):
    UPCAST              = "upcast"               # run upcast_ref chain (from_v→current), then RESUME
    REJECT_AND_PRESERVE = "reject_and_preserve"  # do NOT resume; if value-bearing, run compensation BEFORE retire; else just retire
    DROP                = "drop"                 # clear the row (ONLY legal when bears_value=False)

@dataclass(frozen=True)
class VersionedRow:                    # the NORMALIZED row shape resolve_versioned_load reads (heterogeneous stores → one shape)
    row_id: str                        # the store's PK value (stringified) — the retire/compensation target
    version: int                       # the payload's persisted schema version
    payload: Mapping[str, Any]         # the versioned payload blob (JSONB → dict)
    guild_id: int | None               # for the compensation authority + the once() key

@dataclass(frozen=True)
class StoreSpec:                       # EXTENDS design-spec §2.8 — the base 6 fields are unchanged
    table: str                         # [S]
    sole_writer: "HandlerRef | EngineRef"  # [S]
    retention: str                     # [S]
    checkpoint_class: CheckpointClass  # [S]
    invariant_tag: str                 # [S] INV-F/G/K — money/audit tags drive the fence below
    reader_domains: tuple[str, ...]    # [S]
    # ---- NEW payload-version fields (the undesigned gap — T2-7) ----
    payload_version: int = 1           # [S] the CURRENT schema version of this store's payload
    bears_value: bool = False          # [S] True ⇒ the payload holds money/audit-bearing data (bet, escrow, pot)
    version_policy: VersionPolicy = VersionPolicy.REJECT_AND_PRESERVE  # [S] default; see fence §3.4 + the owner-gated fork §8.1
    active_rows_ref: "ProviderRef | None" = None  # [S] a REGISTERED reader (store_spec,*,conn)->tuple[VersionedRow,...]; REQUIRED iff this store is swept by run_recovery
    retire_ref: "WorkflowRef | None" = None       # [S] the AUDITED row-retire mutation (row_id)->delete/clear; REQUIRED iff version_policy==DROP OR (REJECT_AND_PRESERVE AND not bears_value)
    upcast_ref: "WorkflowRef | None" = None       # [S] REQUIRED iff version_policy==UPCAST; a per-rung (from_v, payload)->payload chain
    compensation_ref: "WorkflowRef | None" = None # [S] REQUIRED iff version_policy==REJECT_AND_PRESERVE AND bears_value; a CompoundOpSpec whose ORDERED DB legs REFUND then RETIRE atomically
```

**Why `active_rows_ref` + `retire_ref`, not generic column strings.** Stores are heterogeneous
(`rps_tournament`, `game_state`, `blackjack` differ in PK name, payload column, and their "active"
predicate). Rather than assume `row.version`/`row.state`/`row.id`, the domain registers a **reader**
(`active_rows_ref`, a `ProviderRef` per vocab §⑩ `refs.py`) that normalizes its rows to `VersionedRow`,
and a **retire mutation** (`retire_ref`, a `WorkflowRef` → the audited delete/clear). The kernel primitive
reads and writes only through those two declared seams — never a generic per-store schema guess.

### 3.3 `sb/kernel/versioning/resolve.py` — the load-time primitive (the upcast primitive `game_state_service` lacks)

```python
@dataclass(frozen=True)
class LoadDisposition:
    action: Literal["resume", "compensated_and_retired", "rejected_and_retired", "dropped", "quarantined"]
    payload: Mapping[str, Any] | None         # upcast/current payload on RESUME; else None
    compensation_result: "WorkflowResult | None"   # the refund's audited result on compensated_and_retired (07 design type); else None
    finding: str | None                       # set on 'quarantined' (broken UPCAST rung) — the operator finding text

async def resolve_versioned_load(spec: StoreSpec, row: VersionedRow, *,
                                 ctx: "WorkflowContext", engine: "WorkflowEngine",
                                 idempotency, db) -> LoadDisposition: ...
```

`resolve_versioned_load` fixed algorithm (buildable, zero further decisions):

| # | Condition | Action |
|---|---|---|
| 0 | `row.version == spec.payload_version` | `resume`, `payload = row.payload` (no policy — the common path). **Return.** |
| 1 | `version_policy == UPCAST` | run `upcast_ref` chain `from row.version → payload_version` (each rung `(from_v, payload)->payload`). **All rungs present** ⇒ `resume` the upcast payload (**Return**). **A missing rung** ⇒ do **not** resume a partly-upcast payload and do **not** fall into REJECT: return `quarantined` (`payload=None`, `finding="upcast_chain_broken:{table}:{row.version}->{payload_version}"`) — the row is **left in place** for an operator, never deleted, never refunded. **Return.** |
| 2 | `version_policy == DROP` | (legal only if `not bears_value` — else the fence §3.4 rejects it at compile) run `retire_ref` (the audited delete) under `once()`; return `dropped`. **Return.** |
| 3 | `version_policy == REJECT_AND_PRESERVE` **and** `bears_value` (⇒ `compensation_ref` is present, fence §3.4) | **the refund-before-delete class fix.** `key = IdempotencyKey(namespace=f"{spec.table}.version_reject", guild_id=row.guild_id or 0, dedup_token=f"{row.row_id}:{row.version}")`. `async with db.transaction() as conn:` → `if once(key, conn):` run `engine.run_ref(compensation_ref, ctx, conn=conn)` — a `CompoundOpSpec` whose **ordered DB legs refund THEN retire the row**, so refund-before-delete is *leg order inside one txn* (07 gives the atomicity); `record_outcome(key, result.outcome, result_ref=result.mutation_id, conn)`; **else** `read_outcome` (reproduce — no double-refund). Return `compensated_and_retired`. **The row is retired ONLY as the compensation's final leg, inside the same txn** — a crash between refund and retire re-enters and `once()` no-ops the refund. **If the compensation FAILS, the row is NOT retired** (07 rolls the whole txn back; status left for retry/operator finding) — the deliberate improvement over the #1693 stopgap (FJ §5 residual gap 1). |
| 4 | `version_policy == REJECT_AND_PRESERVE` **and** `not bears_value` (⇒ `compensation_ref` is `None`) | **nothing to compensate** — a non-value store has no money to refund. Run `retire_ref` (the audited delete) under `once()` (same key shape as row 3). Return `rejected_and_retired`. (This is the case the earlier draft crashed on by unconditionally calling a `None` `compensation_ref`.) |

`run_recovery(store_spec, *, ctx_factory, engine, idempotency, db)` is the **generated** boot/cog-load
sweep:

```python
reader = refs.resolve_provider(store_spec.active_rows_ref)      # the domain-registered VersionedRow reader
async with db.transaction() as conn:                            # a read snapshot; each disposition owns its own write txn
    rows = await reader(store_spec, conn=conn)
for row in rows:
    disp = await resolve_versioned_load(store_spec, row, ctx=ctx_factory(row), engine=engine, idempotency=idempotency, db=db)
    if disp.action == "quarantined": record_operator_finding(disp.finding)   # never deletes
```

This one function replaces every hand-written `recover_*` branch — RPS/blackjack/game_state all declare a
`StoreSpec` (with `active_rows_ref` + `retire_ref`/`compensation_ref`) and call it; none writes a
drop-vs-refund `if`. **`active_rows_ref` is a domain-registered `ProviderRef`, not a due-queue DB
primitive** — the seam that enumerates "active rows of an arbitrary store" lives with the store's domain,
resolved through the K2 ref table (§3.5 note).

### 3.4 The compile fences

```python
# sb/kernel/versioning/compile.py — the version_policy_declared fence
```
- A `StoreSpec` with `bears_value=True` and `version_policy == DROP` ⇒ `SEMANTIC_VIOLATION`
  ("value_bearing_store_cannot_drop") → CI-red. **This is the RPS-forfeit shape, made unbuildable.**
- `version_policy == UPCAST` without `upcast_ref` ⇒ `SEMANTIC_VIOLATION`.
- `version_policy == REJECT_AND_PRESERVE` **and** `bears_value=True` **and** no `compensation_ref` ⇒
  `SEMANTIC_VIOLATION` ("value_reject_needs_compensation").
- `version_policy == DROP`, **or** (`REJECT_AND_PRESERVE` **and** `not bears_value`), **without**
  `retire_ref` ⇒ `SEMANTIC_VIOLATION` ("retire_path_needs_retire_ref") — the row-4/row-2 retire has no writer otherwise.
- Any `StoreSpec` swept by `run_recovery` (any `bears_value` or `checkpoint_class==SESSION` store)
  **without** `active_rows_ref` ⇒ `SEMANTIC_VIOLATION` ("recovery_needs_reader").
- **Task-fire audit fence (mirrors ③.4):** a `ManagedTaskSpec` whose fire mutates (declared `effect="mutating"`)
  MUST carry a `handler: WorkflowRef` (the audited K7 engine), never a bare `HandlerRef` — else
  `SEMANTIC_VIOLATION`.
- **Scheduler-fire = pure-DB fence (consumes 07 §3.6 `atomic_db_only`).** Every `CompoundOpSpec` reachable
  as a `ManagedTaskSpec.handler` `WorkflowRef` is, by 07's `atomic_db_only` fence, **pure-DB + `AT_LEAST_ONCE`
  emits only** — no EFFECT legs, no `BEST_EFFORT` emits, no `confirmation`. This is *why* the fire can ride
  the scheduler's own txn (§3.7). **Discord output from a scheduled fire is an `AT_LEAST_ONCE` outbox emit**
  (a row `run_ref` writes in my fire txn, delivered post-commit by ⑥'s relay), **never** a post-commit
  EFFECT leg. 09 does not re-declare `atomic_db_only`; it consumes 07's and states the consequence here.

### 3.5 `sb/kernel/db/scheduler.py` — the due-queue DB primitive (asyncpg only)

```python
@dataclass(frozen=True)
class DueTimer:
    task_id: str                  # uuid — PK, the timer identity
    task_key: str                 # ManagedTaskSpec.name — the fire target ref + the once() namespace
    guild_id: int | None          # None for GLOBAL scope
    trigger_kind: str             # TriggerKind value
    fire_at: datetime             # when it is due
    payload: Mapping[str, Any]    # the fire's ctx params (JSONB)
    payload_version: int          # for the version policy on the timer's own payload
    recurring: bool               # advance fire_at vs delete after fire
    # ---- misfire / trigger params (denormalized from the spec at arm time — self-contained at fire time) ----
    misfire_policy: str
    catch_up: bool
    grace_s: int
    max_catchup: int
    interval_seconds: int | None  # set iff trigger_kind==interval — drives _next_fire_at
    cron_expr: str | None         # set iff trigger_kind==cron   — drives _next_fire_at
    error_policy: str
    # ---- lease / attempts / lifecycle state ----
    status: str                   # pending | claimed | dead | cancelled  (one-shot success = DELETE; recurring success = advance→pending)
    claimed_by: str | None        # instance/lease holder id
    lease_expires_at: datetime | None
    attempts: int                 # transient re-claim count for the CURRENT fire_epoch (reset on advance)
    consecutive_failures: int     # non-retryable failures across slots — drives DISABLE_AFTER_N
    created_at: datetime
    updated_at: datetime

MAX_FIRE_ATTEMPTS = 12    # transient re-claim cap for one fire_epoch → DEAD + operator finding (mirrors the outbox)

async def arm(timer: DueTimer, *, conn) -> None
#   recurring: INSERT … ON CONFLICT (task_key, guild_id) WHERE recurring DO NOTHING  (idempotent — a live/advanced slot is NOT reset)
#   one-shot : plain INSERT (one-shots free-multi; no slot key)
async def claim_due(now: datetime, *, limit: int, lease_s: int, instance_id: str, conn) -> tuple[DueTimer, ...]
async def mark_fired(timer: DueTimer, next_fire_at: datetime | None, *, conn) -> None
#   next_fire_at is None (one-shot) ⇒ DELETE the row.
#   next_fire_at given (recurring) ⇒ UPDATE status='pending', fire_at=next_fire_at, attempts=0, claimed_by=NULL, lease_expires_at=NULL.
#   ↑ the recurring ADVANCE runs INSIDE the fire txn (§3.7) — there is no separate post-commit rearm, so no crash-after-commit-before-rearm window.
async def mark_failed(task_id: str, error: str, *, retryable: bool, conn) -> DueTimer  # attempts++ or consecutive_failures++, returns the row for the caller to route error_policy
async def mark_dead(task_id: str, finding: str, *, conn) -> None                       # status='dead' (transient cap hit) — terminal; caller records the operator finding
async def reap_expired_leases(now: datetime, *, conn) -> int    # status=claimed & lease_expires_at<now -> pending
async def select_overdue(now: datetime, *, conn) -> tuple[DueTimer, ...]   # READ-ONLY diagnostic (dashboard); boot uses claim_due (§3.7)
async def cancel(task_id: str, *, conn) -> int
async def cancel_scope(guild_id: int, *, conn) -> tuple[DueTimer, ...]     # guild-leave reclaim (C-8) — returns cancelled value-bearing timers for compensation
```

`claim_due` is the **dual-instance-safe** claim — the fix for the uuid-defeated `claim_run`, and the
**bounded** boot-reconcile primitive (§3.7):

```sql
UPDATE sb_due_queue SET status='claimed', claimed_by=$4,
       lease_expires_at = $1 + ($3 || ' seconds')::interval, attempts = attempts + 1
 WHERE task_id IN (
     SELECT task_id FROM sb_due_queue
      WHERE status='pending' AND fire_at <= $1
      ORDER BY fire_at
      FOR UPDATE SKIP LOCKED
      LIMIT $2 )
RETURNING *;
```

### 3.6 `sb/kernel/scheduler/poll.py` — the shared poll infra

```python
@dataclass(frozen=True)
class LaneTickResult:
    lane: str; claimed: int; fired: int; failed: int; skipped: int

class PollLane(Protocol):
    name: str
    async def tick(self, now: datetime) -> LaneTickResult: ...       # claim + process one cycle's due work
    async def reconcile_on_boot(self, now: datetime) -> None: ...    # one-time overdue catch-up (default no-op)

class PollSupervisor:
    def __init__(self, *, lifecycle, clock=SYSTEM_CLOCK) -> None: ...  # K5 lifecycle port (RUNNING/drain), a clock
    def register_lane(self, lane: PollLane) -> None: ...               # composition root registers DueQueueLane + ExpiryJanitorLane
    async def run_forever(self, *, poll_interval_s: int = 5) -> None: ...
    #  - ALWAYS-ON: spawned by the K5 task supervisor as ONE supervised task; NO enablement flag (retires OFF-by-default)
    #  - waits for lifecycle RUNNING before the FIRST reconcile_on_boot (vocab §⑤.5 ready-gate)
    #  - each tick: if NOT lifecycle.can_accept_commands() (DRAINING) -> skip claiming (drain gate, vocab §⑤.2)
    #  - per-lane exception isolation: a lane raising is caught+logged; the loop continues (shipped supervised pattern)
```

**Construction / wiring.** The composition root (under K5) builds `PollSupervisor(lifecycle, clock)`,
constructs `DueQueueLane(engine, scheduler_db, refs, clock, instance_id)` and the draft
`ExpiryJanitorLane(draft_store, clock)` (06 §3.3), `register_lane`s both, and hands
`supervisor.run_forever` to the K5 task supervisor. **The outbox `RELAY_TASK` is NOT registered here** —
it is ⑥'s own supervised `ManagedTaskSpec(Interval 1s)` on the same K5 host, at its own cadence (08 §3.4).
The two share only the K5 RUNNING/drain gate, not this supervisor.

### 3.7 `sb/kernel/scheduler/due_queue.py` — the `DueQueueLane` + the fire

```python
# The canonical system-actor sentinel every scheduled fire runs as (the authority scripted-bypass carrier — §②.3, §12 #1).
SYSTEM_ACTOR = ActorRef(user_id=None, actor_type="system", member_tier=None,
                        is_guild_operator=False, is_bot_owner=False, is_dm=False)

class DueQueueLane:                    # a PollLane
    async def tick(self, now) -> LaneTickResult          # claim_due(limit) -> apply_misfire -> _fire each
    async def reconcile_on_boot(self, now) -> None        # arm_declared_tasks -> reap -> BOUNDED claim-loop -> misfire -> _fire
    async def arm_declared_tasks(self, now) -> None        # first-boot arm of every DURABLE recurring ManagedTaskSpec (idempotent)
    async def arm_task(self, spec: ManagedTaskSpec, *, guild_id=None, payload=None) -> str   # recurring
    async def arm_one_shot(self, spec: ManagedTaskSpec, fire_at: datetime, *, guild_id=None, payload=None) -> str
    async def cancel_task(self, task_id: str) -> None

async def _fire_one(timer: DueTimer, fire_epoch: int, next_fire_at: datetime | None, *,
                    engine, idempotency, scheduler_db, db, clock) -> "WorkflowResult | None":
    key = IdempotencyKey(namespace=timer.task_key, guild_id=timer.guild_id or 0,
                         dedup_token=f"{timer.task_id}:{fire_epoch}")   # DETERMINISTIC — not uuid4
    async with db.transaction() as conn:                                # ONE scheduler-owned txn — the whole fire is atomic
        if not await once(key, conn=conn):
            return _reproduce(await read_outcome(key, conn=conn))       # already fired — no-op replay
        ctx = WorkflowContext(actor=SYSTEM_ACTOR, guild_id=timer.guild_id or 0,   # actor_type="system" ⇒ authority scripted-bypass §②.3
                              request_id=key.render(), params=timer.payload, clock=clock, correlation_id=None)
        result = await engine.run_ref(timer.handler, ctx, conn=conn)    # 07 external-conn: pure-DB legs + central audit + AT_LEAST_ONCE enqueue on MY conn; no txn, no once(), no EFFECT (07 §3.2/§3.6)
        await record_outcome(key, result.outcome, result_ref=result.mutation_id, conn=conn)
        await scheduler_db.mark_fired(timer, next_fire_at, conn=conn)    # one-shot: DELETE · recurring: ADVANCE to next_fire_at — IN THIS TXN
    return result
```

`_fire(timer, decision)` drives `_fire_one` per epoch (COALESCE ⇒ one; FIRE_ALL ⇒ ≤`max_catchup`), passing
`next_fire_at` only on the **last** epoch so the recurring slot advances exactly once after the replay set;
the row stays `claimed` (leased) across a multi-epoch replay and a mid-replay crash simply re-leases and
recomputes (already-fired epochs hit `once()`=False). Because `run_ref` runs on **my** `conn`, opens no
txn and no `once()` of its own (07 §3.2 external-conn), the K7 effect + the central audit + `once()` +
`mark_fired`/advance **all commit atomically in this one txn** — the §3.8 crash reasoning holds.

**`apply_misfire` (pure, `misfire.py`)** — the recurring/one-shot decision:

```python
@dataclass(frozen=True)
class MisfireDecision:
    fire_epochs: tuple[int, ...]     # epochs to fire NOW, each its own once() key
    next_fire_at: datetime | None    # advance the recurring slot here; None ⇒ one-shot (delete after fire)
    truncated: bool                  # FIRE_ALL exceeded max_catchup — an operator finding is recorded

def apply_misfire(timer: DueTimer, now: datetime) -> MisfireDecision: ...
```

- **One-shot (`not recurring`):** **always fire once when overdue** — `fire_epochs=(epoch(fire_at),)`,
  `next_fire_at=None`. `catch_up`/`misfire_policy` **do not apply to one-shots** (recommended resolution of
  the "overdue one-shot with catch_up=False" ambiguity: a one-shot cannot re-arm forward, so an overdue
  one-shot always fires exactly once). `mark_fired(None)` then DELETEs it.
- **Recurring, on time (`fire_at + grace_s >= now`):** `fire_epochs=(epoch(fire_at),)`,
  `next_fire_at = _next_slot(timer, after=fire_at)`.
- **Recurring, overdue beyond grace:**
  - `catch_up=False` **or** `SKIP` ⇒ `fire_epochs=()` (drop the missed window), `next_fire_at =
    _next_slot(timer, after=now)` (re-arm forward, never back-fire).
  - `COALESCE` (default) ⇒ `fire_epochs=(epoch(fire_at),)` (ONE fire), `next_fire_at = _next_slot(timer,
    after=now)` (skip the intermediate missed slots).
  - `FIRE_ALL` ⇒ enumerate missed slots `[fire_at, +interval, …] <= now`; take the first `max_catchup` →
    `fire_epochs`; `truncated = missed > max_catchup`; `next_fire_at = _next_slot` after the last replayed
    slot (or after `now` if truncated — bounded, plus an operator finding).
- `_next_slot(timer, after)`: interval ⇒ smallest `fire_at + k*interval_seconds > after`; cron ⇒
  `croniter(cron_expr).next(after)` (§9 parser deferral).

**`reconcile_on_boot(now)` — bounded, dual-instance-safe (the §8 bound made real):**

```python
await self.arm_declared_tasks(now)                # first-boot: arm every DURABLE recurring ManagedTaskSpec (idempotent — arm's ON CONFLICT DO NOTHING)
async with db.transaction() as conn:
    await scheduler_db.reap_expired_leases(now, conn=conn)   # crashed-mid-fire timers -> pending
while True:                                        # BOUNDED batches, drains monotonically (fired slots advance past now / one-shots delete)
    batch = await scheduler_db.claim_due(now, limit=BOOT_BATCH, lease_s=self.lease_s, instance_id=self.instance_id, conn=<own txn>)
    if not batch: break
    for timer in batch:
        await self._fire(timer, apply_misfire(timer, now))
```

Boot uses **the same `claim_due` SKIP-LOCKED path** as steady-state, so (a) fan-out is bounded by
`BOOT_BATCH` per iteration and drains across iterations — a large overdue backlog never stampedes the
engine/economy (§8), and (b) two instances booting concurrently cannot double-claim the same timer.
`select_overdue` is retained **only** as a read-only dashboard diagnostic, never the fire path.

**`arm_declared_tasks` (first-boot arming — the missing manifest path).** `sb_due_queue` is a fresh table;
boot-reconcile fires only *existing* rows, so a declared `DURABLE` recurring `ManagedTaskSpec` (GC sweeps,
digests) needs a first-ever arm. For each such spec in the manifest: `arm_task` if no live slot exists —
`arm`'s `INSERT … ON CONFLICT (task_key, guild_id) WHERE recurring DO NOTHING` makes this **idempotent**:
on the first boot ever it inserts with `fire_at = _next_slot(now)`; on every later boot a live (possibly
already-advanced) slot exists → the arm is a no-op, so a fire that advanced the slot is never reset. (An
`arm_one_shot` from a producer is armed by the producer when the timer is created — never here.)

### 3.8 Error / failure modes (classified through `from_exception` ①)

| Failure | `error_class` / outcome | Behavior |
|---|---|---|
| fire handler raises `transient` (DB/Discord busy) | `transient` / `DISCORD_FAILED` | txn rolls back, no `record_outcome`, no `mark_fired`/advance; lease expires → re-claimed → retried; `attempts++`. **At `attempts >= MAX_FIRE_ATTEMPTS` ⇒ `mark_dead` + operator finding** (stops the infinite retry against a wedged DB; mirrors the outbox DEAD). |
| fire handler raises `bug`/`user_error` (non-retryable) | `bug`/`user_error` / `BLOCKED` | `mark_failed(retryable=False)`; **does not re-claim** (won't succeed on retry). `error_policy` acts: **`LOG`** ⇒ log a WARNING, then advance (recurring, next slot) / delete (one-shot) — the schedule survives, *this* bad slot is skipped; **`DISABLE_AFTER_N`** ⇒ `consecutive_failures++`; at N ⇒ `cancel` the timer + finding, else advance/delete; **`ESCALATE_FINDING`** ⇒ record an operator finding, then behave as `LOG` (advance/delete). |
| crash mid-fire (after `once()`, before commit) | — | txn rolls back atomically (nothing persisted, key not held, slot not advanced); re-claim fires clean. |
| crash mid-fire (after commit) | — | the effect + `once()` key + `mark_fired`/advance committed **together** (one txn) — nothing is half-done. A recurring slot is already at its new `fire_at`; a one-shot is already deleted. No re-fire (no un-marked window). |
| `compensation_ref` fails during REJECT_AND_PRESERVE | classified by K7 | **row NOT retired** (07 rolls the whole txn back; improvement over #1693); retry-safe via `once()`; operator finding. |
| UPCAST chain has a missing rung | `bug` (quarantine) | `resolve_versioned_load` returns `quarantined` — row **left in place**, operator finding, never resumed/refunded/deleted (a distinct terminal, not the REJECT compensation path). |
| lease expires while fire genuinely still running (slow fire) | — | double-claim possible, but `once()` makes the second fire a no-op replay — correctness preserved, at worst one wasted attempt. |

---

## 4. Provides / Consumes

### Provides (owned canonical shapes — everyone else consumes these)

| Shape | Where | Consumers |
|---|---|---|
| `ManagedTaskSpec` durability/misfire/catch-up fields (completes design §2.8) | `sb/spec/scheduler.py` | every subsystem declaring a durable task; **the outbox `RELAY_TASK` is written in this grammar (08 §3.4)**; the compiler fence |
| `StoreSpec` `version_policy`/`active_rows_ref`/`retire_ref`/`upcast_ref`/`compensation_ref` (completes design §2.8) | `sb/spec/versioning.py` | every persisted-payload store (game_state, tournament, escrow); the fence |
| `VersionedRow` + `resolve_versioned_load` + `run_recovery` — the load-time upcast/compensate/drop/quarantine primitive | `sb/kernel/versioning/resolve.py` | RPS/blackjack/game_state recovery; any cog-load or boot restore of a versioned payload |
| the **durable due-queue** schema + `claim_due` (SKIP LOCKED lease) + `arm`/`arm_one_shot`/`arm_declared_tasks` | `sb/kernel/db/scheduler.py` + `due_queue.py` | the automation feature; the game one-shot timers; every `DURABLE` recurring `ManagedTaskSpec` |
| **boot-reconcile-fires-overdue-exactly-once** (completes vocab §⑤.5) | `due_queue.py::reconcile_on_boot` | the whole restart-safety pattern |
| the **shared poll host** `PollSupervisor` + `PollLane` port | `sb/kernel/scheduler/poll.py` | the **due-queue lane**, the **draft `select_expired` janitor (06)** — both register as lanes |
| the per-fire idempotency `dedup_token` def (completes vocab §④.2 "scheduler fire"): `f"{task_id}:{fire_epoch}"` | `due_queue.py::_fire_one` | the K3 idempotency substrate |
| `SYSTEM_ACTOR` (the system-fire `ActorRef` sentinel, `actor_type="system"`) | `due_queue.py` | any headless kernel fire needing the authority scripted-bypass |

### Consumes (assumed sibling shapes — exact assumption stated)

| Shape | Assumed source | Exact assumption |
|---|---|---|
| `IdempotencyKey`, `once`/`record_outcome`/`read_outcome`, `db.transaction()` | K3 / spec 05 (frozen ④/⑤) | `once(key,*,conn)->bool` (INSERT…ON CONFLICT DO NOTHING); `db.transaction()` yields a txn-bound `conn` (verified `pool.py:170-182` per 07); namespace `task_key` reserved via K1 |
| **`WorkflowEngine.run_ref(ref, ctx, *, conn) -> WorkflowResult`** | K7 / `07-workflow-engine.md` §3.2 | **PROVIDED and named "the scheduler `_fire` target (09:299)".** External-conn mode: resolves the `WorkflowRef`→`CompoundOpSpec` (registry), runs the **DB legs + one central audit row + `AT_LEAST_ONCE` enqueue on MY `conn`**, opens **no** txn, calls **no** `once()`/`record_outcome` (I own dedup), runs **no** EFFECT/`BEST_EFFORT` legs (I own commit). `WorkflowResult.outcome` on the frozen §2.7 five; `result.mutation_id` present. The `atomic_db_only` fence (07 §3.6) guarantees a scheduler-fired spec is pure-DB — so wrapping the fire + `once()` + `mark_fired` in **my** one txn is sound (§3.7). Discord output rides an `AT_LEAST_ONCE` outbox emit (07 writes the row on my conn; ⑥ delivers it), **not** an EFFECT leg. |
| `IdempotencyPosture` enum | K7 / `07-workflow-engine.md` §3.1 | consumed only on the *fired workflow's* `CompoundOpSpec` (07 owns it); **09 does not reference it** (the leaf inversion is retired, §3.1/§12 #2) |
| `resolve_authority` scripted-bypass | K6 / spec 04 (frozen ②.3) | K7 builds `AuthorityRequest(spec.authority_ref, actor…)` and **maps `AuthorityRequest.actor_type = ctx.actor.actor_type`** (seam-correction §12 #1). `SYSTEM_ACTOR.actor_type="system"` ⇒ step-1 scripted bypass ⇒ `allowed=True`; scheduled tasks are not authority-gated. |
| `from_exception(exc,*,surface,target)->ErrorEnvelope` + `Result` | K8 / spec 02 (frozen ①) | every fire/compensation exception classified through it; `error_class`→outcome per the frozen table; `surface="scheduler"` (a new `Surface` member is optional-additive) |
| `emit_audit_action` (11 fields) | shipped `audit_events.py:52` (③) | the fire's mutation audits **inside** K7's `run_ref` (the central row, on my conn); the due-queue's own arm/claim/fire bookkeeping is scheduler-internal state (like draft staging), **not** an auditable mutation |
| `ActorRef` gains `actor_type: str = "user"` | K8 / spec 02 (frozen ⑩) | `ActorRef` today carries `{user_id, is_guild_operator, is_bot_owner, is_dm, member_tier}` and no `actor_type`. It **must add `actor_type: str = "user"`** so `SYSTEM_ACTOR` can carry `"system"` into K7's `AuthorityRequest` — the same additive-field cross-spec correction RC-12 made for `member_tier` (§12 #1). |
| `active_rows_ref` / `retire_ref` / `compensation_ref` / `upcast_ref` resolution | K2 ref table + the store's domain | `refs.resolve_provider(active_rows_ref) -> reader`; `refs.resolve(retire_ref/compensation_ref/upcast_ref) -> CompoundOpSpec`. The domain registers each; the kernel never guesses a store schema. |
| the draft `ExpiryJanitorLane` (a `PollLane`) | draft sibling 06 §3.3/§6 | wraps `draft.store.select_expired(now)` (READ) → `update_status(EXPIRED)`; and the stuck-`APPLYING` sweep (06 §6). Registered on my supervisor (06 §11 confirms 09 hosts it). |
| the outbox `RELAY_TASK` `ManagedTaskSpec(Interval 1s)` | outbox sibling ⑥ / `08-event-outbox.md` §3.4 | ⑥'s relay is its **own** supervised task on the K5 host — NOT a lane on my supervisor, NOT boot-reconciled by me (08 §8 fork E: "the first post-`/ready` poll IS the reconcile"). I supply only the durability grammar it is declared in; I neither poll it nor own its 1s cadence. |
| `lifecycle.can_accept_commands()` / RUNNING predicate + the task supervisor host | K5 / spec 05 (frozen ⑤.2/⑤.5) | RUNNING-only before first reconcile; DRAINING ⇒ stop claiming; K5 spawns `PollSupervisor.run_forever` **and** ⑥'s `RELAY_TASK` as two supervised tasks |
| base `ManagedTaskSpec` / base `StoreSpec` fields | design-spec §2.8 | I extend, not replace — the 5/6 base fields are verbatim |

---

## 5. Data model + migration / index shape

Fresh chain (design §5.2 — no legacy carry). One new table; the version policy reuses the shared
`idempotency_keys` (K3) — **no version table of its own.**

```
sb_due_queue
  task_id             uuid  PRIMARY KEY
  task_key            text  NOT NULL            -- ManagedTaskSpec.name (namespace task_prefix)
  guild_id            bigint                    -- NULL = GLOBAL scope
  trigger_kind        text  NOT NULL            -- interval | cron | one_shot
  fire_at             timestamptz NOT NULL
  payload_json        jsonb NOT NULL DEFAULT '{}'
  payload_version     int   NOT NULL DEFAULT 1
  recurring           boolean NOT NULL          -- advance fire_at vs delete after fire
  -- misfire / trigger params (denormalized from the spec at arm time — self-contained at fire time) --
  misfire_policy      text  NOT NULL
  catch_up            boolean NOT NULL DEFAULT true
  grace_s             int   NOT NULL DEFAULT 0
  max_catchup         int   NOT NULL DEFAULT 1
  interval_seconds    int                       -- NOT NULL iff trigger_kind='interval'
  cron_expr           text                      -- NOT NULL iff trigger_kind='cron'
  error_policy        text  NOT NULL
  -- lease / attempts / lifecycle --
  status              text  NOT NULL DEFAULT 'pending'  -- pending | claimed | dead | cancelled
  claimed_by          text                      -- instance/lease holder id
  lease_expires_at    timestamptz               -- crash-during-fire recovery TTL
  attempts            int   NOT NULL DEFAULT 0   -- transient re-claim count for the current fire_epoch (reset on advance)
  consecutive_failures int  NOT NULL DEFAULT 0   -- non-retryable failures across slots (DISABLE_AFTER_N)
  created_at          timestamptz NOT NULL
  updated_at          timestamptz NOT NULL
  INDEX (status, fire_at)                                  -- claim_due / select_overdue hot path
  INDEX (status, lease_expires_at) WHERE status='claimed'  -- reap_expired_leases
  INDEX (guild_id) WHERE guild_id IS NOT NULL              -- cancel_scope (guild-leave reclaim)
  UNIQUE (task_key, guild_id) WHERE recurring              -- one live slot per recurring task; arm's ON CONFLICT DO NOTHING rides it; one-shots free-multi
```

**Status lifecycle.** A one-shot's success is a **DELETE** (no terminal status); a recurring timer's
success is an **advance** back to `pending` with a future `fire_at` (so `select`/`claim_due`, which key on
`status='pending' AND fire_at<=now`, correctly skip a just-advanced slot). The only resting non-`pending`
states are `claimed` (leased, mid-fire) and the terminals `dead` (transient cap `MAX_FIRE_ATTEMPTS` hit —
operator finding) / `cancelled` (`DISABLE_AFTER_N` / `cancel` / guild-leave). There is no lingering
`fired`/`failed` resting state — a recurring bad slot either advances (LOG/ESCALATE) or is cancelled.

**Dedup key (the fire-time exactly-once guard, ④):** a row in the shared `idempotency_keys` table
(K3), `key = "{task_key}:{guild_id}:{task_id}:{fire_epoch}"`, minted per fire inside the fire txn.
`fire_epoch = int(fire_at.timestamp())` — **deterministic**, so two instances (or a boot re-fire)
collide on the same key and exactly one fires. This is the structural fix for the shipped
`_idempotency_key`'s uuid4 (§1). The **version-reject** guard reuses the same table:
`key = "{table}.version_reject:{guild_id}:{row_id}:{from_version}"`.

**Importer (§5.2):** `automation_rules` (user-authored recurring automations) import name-stable as a
**domain store** whose rows arm kernel timers at boot (via a producer, not `arm_declared_tasks`, which is
for *manifest-declared* tasks); `automation_runs` (transient claim ledger) is **not imported**
(superseded by the due-queue lease). Live in-memory one-shot `asyncio.sleep` timers have no persisted rows
to import — they simply become durable from cutover forward.

---

## 6. Restart & merge=deploy behavior (exactly-once)

| Concern | Behavior |
|---|---|
| **Durable timers** | `DURABLE` tasks are DB rows in `sb_due_queue` — survive a merge=deploy restart. `IN_MEMORY` tasks reset (matches shipped; declared, never implicitly lossy — vocab §⑤.1). ⑥'s `RELAY_TASK` is `IN_MEMORY` (its durability is the `event_outbox` rows, not a timer) — a peer supervised task, not in my due-queue. |
| **First-boot arming** | `arm_declared_tasks` arms every manifest-declared `DURABLE` recurring `ManagedTaskSpec` that has no live slot (idempotent via `ON CONFLICT (task_key,guild_id) WHERE recurring DO NOTHING`), so GC sweeps / digests exist as rows before the first reconcile. Runs first in `reconcile_on_boot`. |
| **Boot reconcile** | On boot, **after `/ready` reports 200 (RUNNING)** (vocab §⑤.5): `arm_declared_tasks` → `reap_expired_leases` (recover crashed-mid-fire timers) → a **bounded `claim_due(limit)` loop** (SKIP LOCKED, drains the overdue backlog in batches — never a stampede, dual-instance-safe) → `apply_misfire` per timer → `_fire` each under `once()`. Recurring slots advance **inside** each fire txn. |
| **Exactly-once fire** | Every fire is guarded by `once(IdempotencyKey(task_key, guild_id, f"{task_id}:{fire_epoch}"))` **inside** the fire's `db.transaction()` (vocab §④.1). The K7 effect + central audit (`run_ref` on my conn) + `once()` + `mark_fired`/advance commit **together**. A timer overdue across a restart, or claimed by both instances in the fast-release overlap, fires **exactly once**; the second attempt `read_outcome`s and no-ops. |
| **Dual-instance overlap** | Both workers poll sub-second during fast-release. `claim_due`'s `FOR UPDATE SKIP LOCKED` means each row is claimed by exactly one instance; `once()` is the belt-and-braces if a lease is double-granted (lease expiry mid-fire). This is the concrete fix for the uuid4-defeated `claim_run` (§1). |
| **Drain gate** | A `DRAINING` instance stops claiming new fires (`PollSupervisor` checks `can_accept_commands()` each tick — vocab §⑤.2). In-flight fires either finish or their lease expires → the RUNNING instance re-claims. |
| **Misfire (down window)** | Recurring only. `COALESCE` (default, A#7): N missed interval fires ⇒ **one** boot fire + advance past now (accrual-safe). `FIRE_ALL`: replay up to `max_catchup` missed fires (count-exact; a truncated storm gets an operator finding). `SKIP` / `catch_up=False`: drop all missed, re-arm forward. An **overdue one-shot always fires exactly once** (misfire/catch_up do not apply). |
| **Persistent-failure terminal** | A transient fire re-claimed `MAX_FIRE_ATTEMPTS` times ⇒ `dead` + operator finding (no infinite retry). A non-retryable fire is routed by `error_policy` (LOG advance-and-log / DISABLE_AFTER_N cancel-after-N / ESCALATE_FINDING finding-then-advance). |
| **Version-mismatch on restore** | A persisted payload whose `version != StoreSpec.payload_version` after a deploy routes through `resolve_versioned_load`: `REJECT_AND_PRESERVE` refunds-before-delete (value) or just-retires (non-value), `UPCAST` migrates+resumes (or quarantines a broken chain), `DROP` clears (only if `bears_value=False`). Idempotent via `once()` — a crash between refund and retire never double-refunds (they are legs of one compensation txn). |
| **Guild leave (C-8)** | `cancel_scope(guild_id)` cancels guild-scoped timers; value-bearing ones return their rows for `compensation_ref` refund (the on_guild_remove semantics, generalized). Full C-8 wiring is T2-8's (bounded deferral §9). |

---

## 7. Architecture rules honored (INV / layer cites)

- **DB access only through the `utils.db.*` boundary** — all SQL lives in `sb/kernel/db/scheduler.py`
  (asyncpg only). This **retires the raw `pool.get().fetch()` in `automation_scheduler._fetch_due_rules`**
  (`:142-158`, a `utils/db`-boundary violation inside a service) — a cleanup the kernel forces.
- **All mutations through the domain `*_mutation.py` seam + `emit_audit_action`** — a fire **never
  writes a domain row itself**; it delegates to K7 `run_ref`, which routes through the audited
  workflow engine (③.1, "never bypassed") and writes the central audit row on my conn. The version-reject
  **refund** and the **retire** are K7 `WorkflowRef`s (`compensation_ref`/`retire_ref`) → audited. The
  due-queue's own arm/claim/fire status is scheduler-internal state (like draft staging), correctly
  emitting no domain audit.
- **`services` must NOT import `views` (zero-tolerance); cogs never import cogs** — `sb/kernel/scheduler/*`
  and `sb/kernel/versioning/*` (kernel tier) import no view and no cog. The recovery logic moves
  **out of** cog code (`rps_tournament/_persistence.py`, `blackjack_cog.py`) into the kernel — a
  layering improvement. The `sb/spec/scheduler.py` leaf imports **no** kernel module (the
  `IdempotencyPosture` inversion is retired — §3.1/§12 #2).
- **`settings_keys` constants, never raw keys** — the shipped `AUTOMATION_SCHEDULER_ENABLED` env read
  is retired (the kernel loop is always-on); any residual automation-feature gate becomes a
  `ConfigSpec` (vocab ⑥), never a raw `os.getenv`.
- **INV-F (audited-money boundary)** — the version-reject refund flows through the escrow/economy
  `CompoundOpSpec` (07's `game_wager_workflow` family), keeping every coin movement inside one audited
  txn. `bears_value=True` stores carry `invariant_tag` INV-F, feeding the fence.
- **Namespace reservation** — `task_key` (ManagedTaskSpec.name) is namespace kind `task_prefix`
  (design §2.8); the `once()` namespaces (`{task_key}`, `{table}.version_reject`) are K1-reserved.

---

## 8. Options → Decision → Why (per fork closed)

| Fork | Options | **Decision** | Why |
|---|---|---|---|
| **Claim/lease** | (a) uuid-random idempotency key [shipped, defeated] · (b) `FOR UPDATE SKIP LOCKED` lease + deterministic `dedup_token` + `once()` | **(b)** | (a)'s `uuid.uuid4()` (`automation_scheduler.py:275`) makes the UNIQUE-key claim collide **never** across instances → double-fire. SKIP LOCKED gives single-claim; deterministic `f"{task_id}:{fire_epoch}"` + `once()` gives exactly-once even under lease-expiry re-claim. |
| **Kernel loop enablement** | (a) env-gated, OFF by default [shipped] · (b) **always-on** | **(b)** | Restart-safety is a kernel invariant, not an opt-in. The shipped OFF default is why "the only durable poller is inert." Individual *feature* lanes (a user automation) may still be independently gated; the poll loop itself is not. |
| **Poll topology** | (a) one supervised loop per feature · (b) **one `PollSupervisor` hosting the due-queue lane + the draft janitor lane; the outbox relay is a peer supervised task** | **(b)** | One host = one lifecycle/drain gate + per-lane isolation for the two *durable-due-queue-adjacent* lanes. The outbox relay chose its **own** `RELAY_TASK(Interval 1s)` (08 §3.4, self-reconciling); source-wins, I do not host it — the 1s vs 5s cadence conflict dissolves because it is not my lane. |
| **Misfire default (A#7)** | (a) fire_all · (b) **coalesce** · (c) skip | **(b) coalesce** | A#7 Tier-3 default; accrual-safe (a timer down 3 days fires once, not 72×). `fire_all`/`skip` are declared opt-ins for count-exact / latest-snapshot tasks. |
| **One-shot timers** | (a) in-memory `asyncio.sleep` [shipped] · (b) **durable `OneShot` ManagedTask** | **(b)** | The shipped sleeps (`blackjack_cog.py:410,572`, `rps _helpers.py:126,192`) are lost every deploy. `OneShot` persists + boot-reconciles; an overdue one-shot fires exactly once. |
| **Where the version policy lives** | (a) cog-delegated branch [shipped] · (b) **declared `StoreSpec` field + one kernel primitive** | **(b)** | (a) is exactly the L-1 hazard — `game_state_service.py:68-72` tells each cog to hand-write resume-vs-refund, and RPS got it wrong. One declared policy + `resolve_versioned_load` makes the branch generated and uniform; DROP-on-value is a compile violation. |
| **Version-reject on comp failure** | (a) clear the row anyway [shipped #1693 stopgap] · (b) **retain the row, retry-safe, operator finding** | **(b)** | The shipped stopgap clears even when the refund fails (FJ §5 residual gap 1) → silent forfeit. `once()` makes retry safe, so there is no infinite-retry reason to forfeit; retain + escalate instead. **The durable class fix is strictly better than the stopgap.** |
| **Reject on a non-value store** | (a) crash on a `None` `compensation_ref` [earlier draft bug] · (b) **just retire the row via `retire_ref` (nothing to compensate)** | **(b)** | A non-value store has no money to refund; `REJECT_AND_PRESERVE` there means "don't resume, retire cleanly." Row 4 of §3.3 + the `retire_ref` fence make it buildable, not a null-deref. |
| **Broken UPCAST rung** | (a) fall through into REJECT/compensation · (b) **quarantine: leave the row, operator finding** | **(b)** | A missing rung is a *bug/config* fault, not a value-reject. Routing it into REJECT would refund-and-delete a row that should be inspected. `quarantined` never deletes — the operator fixes the chain and re-runs. |
| **Fire dedup layers** | (a) lease only · (b) **lease + `once()` belt-and-braces** | **(b)** | The lease prevents double-*claim*; `once()` prevents double-*effect* even when a lease is double-granted. Both, per vocab §⑤.4's fast-release reasoning. |
| **Recurring re-arm timing** | (a) post-commit `rearm_recurring` [earlier draft] · (b) **advance inside the fire txn (`mark_fired` branch)** | **(b)** | (a) leaves a crash-after-commit-before-rearm window that silently stops a recurring task. Folding the advance into the fire txn makes the effect + `once()` + advance atomic — no window (§3.8). |
| **Boot-reconcile pacing** | (a) `select_overdue` then fire all at once [earlier draft — unbounded] · (b) **bounded `claim_due(limit)` loop** | **(b)** | (a) contradicted this row's own "bounded" claim and could stampede the engine/economy at boot. The `claim_due` loop bounds per-iteration fan-out, drains monotonically, and is dual-instance-safe at boot too. |
| **Persistent-failure terminal** | (a) infinite retry / undefined `LOG` [gap] · (b) **`MAX_FIRE_ATTEMPTS`→`dead` + finding; `error_policy` defines LOG/DISABLE_AFTER_N/ESCALATE** | **(b)** | Symmetric with the outbox `MAX_ATTEMPTS=12`→DEAD. `LOG` = fire-and-log each slot forever *by design* (each slot is a distinct fire, not a stuck retry); `DISABLE_AFTER_N` parks after N. No silent stuck-`failed` state. |

---

## 8.1 Open decisions (owner-gated) — the one fork this spec does NOT decide

> A concern is only *landed* if it points to a section that exists. This is that section; §4/§10 point here.
> Everything else in §8 is decided and built. This single fork is a **data-loss policy** — the same class
> as the frozen vocab §⑧ SF-g store-drop `disposition` — so it is surfaced with options + a recommendation,
> **never decided here.**

| # | Fork | Tier / gate | Built default (so the build is unblocked) | The open call | Touches |
|---|---|---|---|---|---|
| **OD-1** | **`StoreSpec.version_policy` default for a `bears_value` store** (T2-7, owner-flagged). When a value-bearing payload's schema drifts across a deploy and no `upcast_ref` covers it, the default policy decides whether the value is preserved. | Tier-2, **owner-gated** (data-loss/data-custody) | `REJECT_AND_PRESERVE` (**recommended** — refund-before-delete, never forfeit; the compile fence forbids `DROP` on a value store, so the *floor* is safe regardless). | Confirm `REJECT_AND_PRESERVE` as the default, **or** require an `UPCAST` path for every `bears_value` store (no loss, higher dev burden), **or** name a per-store override policy. The *mechanism* (all three policies + the fence + `resolve_versioned_load`) is fully built either way; only the **default** is the owner call. | version policy (§3.2/§3.3), the RPS canary, the §⑧ SF-g data-loss-policy class |

**Not open (previously mis-flagged as open, now resolved):** the "K7 external-conn fire seam" is
**settled** — 07 §3.2 already provides `run_ref(ref, ctx, *, conn)` and names 09 as its consumer, so the
scheduler's refund+retire atomicity is real, not a degraded fallback (§4, §12 #3). It carries no open
decision.

---

## 9. Labeled deferrals (each bounded by the capability corpus)

| Deferral | Reason | Bound |
|---|---|---|
| **Cron parser** | The shipped scheduler blocks `scheduled_time` rule creation until cron parsing ships (`_compute_next_run_at` returns `now+1day` defensively). | A bounded impl detail: a vetted 5-field parser (adopt-freely per CLAUDE.md, e.g. `croniter`, pinned) behind `Cron`; `_next_slot` calls it; zero contract change. |
| **Durable cooldown store (SF-e)** | Cooldowns are **read-on-check** (resolver step 3), not **fired** — they are not due-queue timers. | Out of ⑦'s scope. If the owner promotes SF-e, it is a `StoreSpec` aggregate the resolver reads off `CooldownSpec`, not a scheduler concern. Pointer only. |
| **Event-triggered tasks (`TriggerKind.EVENT`)** | Bus-armed, not polled — a different arm path. | Declared in the enum for grammar completeness; the arm path is the EventBus (K4), not the due-queue. Bounded. |
| **Full C-8 guild-leave reclaim wiring** | `cancel_scope` + compensation is provided; the per-guild lifecycle orchestration is T2-8's. | The `cancel_scope` seam returns value-bearing timers for refund; T2-8 wires the trigger. |
| **Compensation saga (refund-of-refund)** | If a `compensation_ref` refund itself needs multi-step rollback. | Out of the v1 corpus (A#26 "record without a saga engine"); v1 retains the row + operator finding. The `compensation_ref` `WorkflowRef` (a K7 `CompoundOpSpec`) is the forward seam. |
| **`FIRE_ALL` catch-up storm beyond `max_catchup`** | A task legitimately needing full replay of a very long down window. | `max_catchup` caps it with an operator finding on truncation (`MisfireDecision.truncated`); unbounded replay is a later band. |

All deferrals sit behind a designed seam; none blocks building the due-queue + the version policy now.

---

## 10. Retirement map (FJ L-rows / §4 gaps / owner-queue items)

| Row (FJ §2 L / §4 gap / §6 owner-queue) | How this spec retires it |
|---|---|
| **L-8 — restart-safety of tasks/timers systematically unbuilt** | Durable `sb_due_queue` + `ManagedTaskSpec` durability/misfire/catch-up + `OneShot` durable timers + `reconcile_on_boot` (bounded claim-loop + first-boot `arm_declared_tasks`) + the always-on `PollSupervisor` (retires the OFF-by-default inert spawn). **CLAIMED / CLOSED.** |
| **L-1 — RPS tournament forfeit STILL LIVE post-#1693** | `StoreSpec.version_policy = REJECT_AND_PRESERVE` **generates** refund-before-delete (refund→retire as legs of one compensation txn); the hand-written `recover_rps_tournament` branch (`_persistence.py:104-115`) is retired; DROP-on-value is a compile violation. **This is the durable CLASS fix** — V-1 (the one-off PR) is the stopgap; my design makes the forfeit structurally unbuildable. **CLAIMED / CLOSED (as the class fix; V-1 remains the immediate PR).** |
| **T2-6 — ManagedTaskSpec durability fields (persistence/misfire/catch-up)** | The `durability`/`misfire_policy`/`catch_up`/`grace_s`/`scope`/`max_catchup` fields + the durable due-queue they drive (§3.1). (The earlier `idempotency` field is dropped as a leaf-inversion fix — §3.1/§12 #2.) Owner-queue Tier-2 recommendation "Yes — required for merge=deploy survival"; a Gate-0 confirm, not a fork. **CLAIMED / CLOSED.** |
| **T2-7 — payload-version-mismatch policy (owner-flagged)** | `VersionPolicy {UPCAST, REJECT_AND_PRESERVE, DROP}` on `StoreSpec` + the `resolve_versioned_load` primitive (resume/upcast/compensate/reject-retire/quarantine) + the `value_bearing_store_cannot_drop` fence. **The DEFAULT is owner-gated (data-loss policy) → landed in §8.1 OD-1 with options + recommendation. CLAIMED / DESIGNED-TO + FLAGGED (§8.1).** |
| **§5 residual gap 1 (#1693) — clear-on-refund-failure forfeit** | REJECT_AND_PRESERVE does **not** retire when the compensation fails (07 rolls the txn back; retry-safe via `once()` + operator finding) — the deliberate improvement over the stopgap. **CLOSED.** |
| **A#7 — missed-window coalesce policy (Tier-3)** | `MisfirePolicy.COALESCE` default; `FIRE_ALL`/`SKIP` declared opt-ins (§3.1, §8); one-shots fire-once. Blessed default. **CLOSED.** |
| **§4 gap — game_state_service has no upcast primitive** | `resolve_versioned_load` is the upcast primitive (`UPCAST` runs `upcast_ref` chain then resumes; a broken chain quarantines); the `:68-72` cog-delegation is retired. **CLOSED.** |
| **§4 item 15 — named canaries have no failure arm** | The scheduler canary (RPS version-bump) gets a failure arm: **boot-reconcile refunds the fee exactly once + no force-delete-before-refund + one-shot survives a simulated deploy** = the pass/fail oracle. **PARTIALLY CLOSED (the timer/version canary; farm-collect's arm is 07's).** |
| **Bonus — the uuid-defeated `claim_run` (a live correctness bug in the one durable poller)** | Deterministic `dedup_token` + SKIP LOCKED lease + `once()` (§1, §8). Retired as part of L-8's closure. |

---

## 11. Build order (K0-K10 placement + what it blocks)

**Placement.** A strand-2 durability kernel function. It has two landing points:
- The **shared poll host** rides on **K5** (design §9.1 "lifecycle + task supervisor") — K5 spawns the
  `PollSupervisor` as one supervised task and provides the RUNNING/drain predicates.
- The **durable due-queue + version policy** land in the **strand-2 durability band (K9-peer)** — after
  **K3** (`once`/`db.transaction()`), **K5** (the `/ready` gate + supervised host), and **K7** (the
  `run_ref` fire target). It is a **peer of the outbox (⑥) and the draft pipeline (06)** — all three
  consume K3; the draft janitor registers a `PollLane` on my supervisor, while the outbox relay runs its
  own supervised `RELAY_TASK`.

**Depends on (must land first):** K3 (idempotency + transaction) · K5 (lifecycle RUNNING/drain +
supervised host) · K6 (authority scripted-bypass for system fires) · K7 (`run_ref` — the audited fire
target, **provided** at 07 §3.2) · K8 (error envelope; **`ActorRef.actor_type` additive field** — §12 #1) ·
K1 (`task_key` `task_prefix` reservation + the `once()` namespaces) · K2 (the ref table resolving
`active_rows_ref`/`retire_ref`/`compensation_ref`/`upcast_ref`).

**Peers (share the K3 substrate; poll topology per §8):** the **outbox relay (⑥)** runs its own
`RELAY_TASK(Interval 1s)` supervised task (08 §3.4); the **draft pipeline (06)** registers
`ExpiryJanitorLane` on **my** `PollSupervisor` (06 §11).

**Internal build order:** (1) `sb/spec/scheduler.py` + `sb/spec/versioning.py` leaves (incl. `VersionedRow`)
→ (2) `sb/kernel/db/scheduler.py` + migration `000N_due_queue.sql` → (3) `sb/kernel/scheduler/poll.py`
(`PollSupervisor` + `PollLane`) → (4) `sb/kernel/scheduler/misfire.py` (pure `apply_misfire`) → (5)
`sb/kernel/scheduler/due_queue.py` (`DueQueueLane` + `_fire` + `arm_declared_tasks`, needs K7 `run_ref` +
`SYSTEM_ACTOR`) → (6) `sb/kernel/versioning/resolve.py` + `compile.py` (the fences) → (7) wire the
`PollSupervisor` into the composition root under K5; register the due-queue + draft-janitor lanes → (8)
**canary:** declare the `rps_tournament` `StoreSpec` (`bears_value=True`, `REJECT_AND_PRESERVE`,
`active_rows_ref=rps_tournament.active_rows`, `compensation_ref=rps_tournament.refund_then_retire`) +
`run_recovery`; write the version-bump oracle test; retire `recover_rps_tournament`.

**Blocks (cannot ship until this lands):**
- **Restart-safe game timers** — blackjack/RPS tournament countdowns + reaction windows become durable
  `OneShot`s; a scheduled fire's Discord output rides an `AT_LEAST_ONCE` outbox emit (§3.4).
- **Every `DURABLE` `ManagedTaskSpec`** across the manifest (automation feature, GC sweeps, digests) —
  `arm_declared_tasks` + the due-queue are the gate.
- **The draft-expiry janitor (06 §3.3/§6)** — `select_expired` + stuck-`APPLYING` sweep ride my lane.
- **Safe cross-deploy persisted state for any `bears_value` store** — the version policy is the gate.

*(The outbox relay is **not** blocked on me — it ships its own supervised loop and reconciles itself
(08 §8 fork E); it only reuses the `ManagedTaskSpec` durability grammar this spec authors.)*

---

## 12. Seam corrections (flagged; source-wins Q-0120)

1. **`ActorRef` needs an `actor_type` field (cross-spec correction for K8/02 + K7).** The system-fire
   authority scripted-bypass (§②.3) keys on `AuthorityRequest.actor_type == "system"`, but the frozen
   `ActorRef` (vocab §⑩) carries `{user_id, is_guild_operator, is_bot_owner, is_dm, member_tier}` and **no
   `actor_type`** — so a `WorkflowContext.actor` has no way to carry "system" into K7's
   `AuthorityRequest`. **Correction:** `ActorRef` gains `actor_type: str = "user"` (the same additive
   cross-spec field RC-12 added for `member_tier`), and K7 maps `AuthorityRequest.actor_type =
   ctx.actor.actor_type` when building the request (07 §3.3 step 1). 09 defines the canonical
   `SYSTEM_ACTOR` sentinel (`actor_type="system"`, §3.7). Without this the scheduled bypass is asserted but
   not carried; with it, it is structural.
2. **`IdempotencyPosture` leaf-inversion retired by removal.** The earlier 09 draft put
   `idempotency: IdempotencyPosture` on `ManagedTaskSpec` (a `sb/spec/` leaf), but 07 homes
   `IdempotencyPosture` in the **kernel** module `sb/kernel/workflow/spec.py` (07 §2) — a leaf importing a
   kernel enum is the exact upward/circular import 08 §12/RC-3 fixed for `DeliveryClass`. **Correction:**
   the field is **dropped** — the scheduler fire is durable-once *by construction* (deterministic `once()`,
   §3.7), so the posture was redundant; the *fired workflow's* posture lives on its `CompoundOpSpec` (07).
   `sb/spec/scheduler.py` now imports nothing from the kernel. (If a future need arises to reference the
   posture from a leaf, the fix is to re-home it to a spec leaf, mirroring `DeliveryClass` → `sb/spec/events.py`;
   flagged but not needed today.)
3. **K7 `run_ref(ref, ctx, *, conn)` is PROVIDED — the earlier "same seam 07 flags / degrades to per-op"
   hedge was stale.** The current `07-workflow-engine.md` §3.2 co-designs three entries and **explicitly
   names `run_ref(ref, ctx, *, conn) → WorkflowResult` "the scheduler `_fire` target (09:299)"**, running
   the DB legs + central audit + `AT_LEAST_ONCE` enqueue on the caller's conn under the `atomic_db_only`
   fence (07 §3.6). **Correction:** 09's `_fire` targets that exact entry (§3.7); the refund+retire
   atomicity (§3.3) is **real**, not a degraded fallback, and there is **no open decision** attached to it
   (removed from §8.1). 06 §12 note 4 independently confirms "09 already assumes exactly this entry."
4. **Outbox topology reconciled to the WRITTEN ⑥ (was "not yet written").** The earlier 09 modelled the
   outbox relay as an `OutboxRelayLane` `PollLane` on my `PollSupervisor` (5s). `08-event-outbox.md` is now
   written and models the relay as its **own** `RELAY_TASK = ManagedTaskSpec(trigger=Interval(1s))`
   supervised by K5, **self-reconciling** (08 §3.4/§8 fork E: "the first post-`/ready` poll IS the
   reconcile"). **Correction:** I do **not** host or boot-reconcile it, and I do **not** own its 1s cadence;
   it is a peer supervised task that merely reuses the `ManagedTaskSpec` durability grammar this spec
   authors. My `PollSupervisor` hosts only the due-queue lane + the draft `ExpiryJanitorLane` (06 §11). The
   "not yet written" text and the 5s-lane assumption are withdrawn.
5. **Read-list cite drift — the in-memory one-shot timers.** The brief cited `rps_tournament_cog.py:274`
   and `blackjack_cog.py:572,410`. Verified real locations: the one-shot `asyncio.sleep`s are
   `blackjack_cog.py:410` (reaction-join window) + `:572` (`sleep(duration_mins*60)` tournament
   countdown), and **`rps_tournament/_helpers.py:126,192`** (`sleep(300)`) — not `rps_tournament_cog.py:274`.
   The class (in-memory one-shots lost on deploy) is confirmed; the RPS location is in `_helpers.py`.
6. **The shipped claim is NOT exactly-once across instances (a live bug, not just a mis-cite).**
   `automation_scheduler._idempotency_key` (`:263-275`) builds `f"rule:{rule_id}:tick:{epoch}:{uuid.uuid4()}"`.
   With `uuid.uuid4()` in the key, two concurrent instances polling the same rule at the same
   `next_run_at` generate **different** keys → both `claim_run` INSERTs succeed (the UNIQUE(idempotency_key)
   never collides) → **double-fire**. The docstring's "so two concurrent schedulers cannot double-run the
   same rule" (`:11-13`) is **false for the merge=deploy overlap**. My due-queue fixes it (deterministic
   `dedup_token` + SKIP LOCKED + `once()`).
7. **`_fetch_due_rules` uses raw `pool.get().fetch()`** (`:142-158`) — a `utils/db`-boundary violation
   inside a service. Retired by moving all SQL to `sb/kernel/db/scheduler.py`; not a divergence, a
   cleanup the kernel forces.
8. **`game_state_service.save()` confirms the delegation gap** — the `version` column exists (`:60`) but
   the docstring (`:68-72`) explicitly delegates resume-vs-refund+clear to "an adopting cog"; there is no
   upcast primitive and no enforced refund-before-delete. `resolve_versioned_load` is that missing primitive.

---

*Written 2026-07-04 against the frozen shared vocabulary (`../shared-vocabulary.md`, all-five-pass) and
reconciled against the three WRITTEN strand-2 siblings (`06-draft-pipeline.md`, `07-workflow-engine.md`,
`08-event-outbox.md`). Spot-verified against shipped source this session: `automation_scheduler.py:1-29,120-297,299-397`,
`utils/db/automation.py:150-295`, `rps_tournament/_persistence.py:80-276`, `rps_tournament/_helpers.py:126,192`,
`blackjack_cog.py:123-300,410,572`, `game_state_service.py:1-120`, `game_state_cleanup.py:40-84`. Sibling
seams verified against the written specs: `07 §3.2` (`run_ref(ref, ctx, *, conn)` + `atomic_db_only` §3.6),
`08 §3.4` (`RELAY_TASK` `ManagedTaskSpec(Interval 1s)`, §8 fork E self-reconcile), `06 §3.3/§11`
(`ExpiryJanitorLane` on 09's supervisor). **NOT SOURCE OF TRUTH for runtime** — a Phase-B design contract
for the strand-2 build to execute against.*
