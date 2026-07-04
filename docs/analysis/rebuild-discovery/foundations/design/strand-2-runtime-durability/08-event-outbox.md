# Strand-2 · ⑥ The Event Outbox / Durable Delivery (K4) — Buildable Design Spec

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B design contract. Precedence: shipped source &
> merged PRs > the five strand-1 specs (for shapes they own) > the frozen `../shared-vocabulary.md`
> > this doc. This doc **builds on** the frozen vocab (§③ audit-row, §④ idempotency-key, §⑤
> restart-safety) and **completes** the two skeletons it left for the outbox: `EventSpec.delivery`
> and the **in-txn outbox** (§④.2 "Leg / relay dedup", §⑤.2 "the outbox's at-least-once delivery").
> It **consumes the poll infrastructure the scheduler sibling ⑦ owns** (`09-scheduler-state.md` §3.6):
> the relay is an `OutboxRelayLane` (a `PollLane`) registered on the shared `PollSupervisor` — it does
> **not** ship its own loop (§12 seam-correction 4; 09 §8 "Poll topology" closed that fork).
> Spot-verified against shipped source this session (cites inline). Design against frozen decisions
> Q-0219…Q-0237 — never re-decided here.

---

## 1. Summary + the exact undesigned gap

**What ⑥ is.** The single durable path from "a committed DB mutation" to "its bus event reached every
subscriber." Today emission is **commit-then-emit *outside* the transaction**: if the process dies (or
a merge=deploy restart lands) between commit and `bus.emit`, the event is gone and "event lost" is only
a log line. ⑥ closes that window by writing the event as a row **inside the same `db.transaction()`
conn** as the effect (so the event exists iff the effect committed), and a post-commit **relay lane**
polls that table and delivers to the bus with at-least-once + handler-dedup semantics.

**Already designed (anti-pad — I do NOT re-derive these):**
- **The producer seam** `outbox.enqueue_all(spec.emits, ctx, result, *, conn)`, `EventEmitSpec`, and the
  `DeliveryClass{AT_LEAST_ONCE, BEST_EFFORT}` split are **declared by the K7 workflow-engine spec**
  (`07-workflow-engine.md:99-119,192,236`, §8 fork F). I **own the delivery-side implementation** of that
  seam **and its return protocol** (§3.3, §12 seam-correction 5 — 07's single-call/step-6 text must change);
  I do not re-derive the enum's two members.
- The idempotency primitives `IdempotencyKey`/`once`/`record_outcome`/`read_outcome` + `idempotency_keys`
  + `db.transaction()` are **owned by K3** (spec 05, vocab §④). I **consume** them — the outbox row's
  dedup key **is** an `IdempotencyKey.render()` (vocab §④.2 row 3).
- **The shared poll infrastructure** `PollSupervisor` / `PollLane` / `LaneTickResult` is **owned by the
  scheduler ⑦** (`09-scheduler-state.md` §3.6). I **register a lane on it**; I own the delivery lane, not
  the loop (09 §4 "I host it on my `PollSupervisor`").
- `emit_audit_action`'s 11-field payload is **shipped** (`audit_events.py:52`, verified) and frozen
  (vocab §③.2). I **consume** it unchanged as the relay's delivered event; I add a durable *twin*, never
  edit its signature. Its `occurred_at` is emitted as an **ISO string** (`audit_events.py:87`
  `occurred_at.isoformat()`; the subscriber `_on_audit_action(occurred_at: str, …, **_extras)` types it
  `str`, verified) — the outbox stores and re-emits that exact string (§6.5 codec).
- The restart-safety skeleton (durable store · drain gate · boot-reconcile after `/ready` 200 ·
  fast-release) is **owned by 05/02 and completed by the scheduler ⑦** (vocab §⑤). I **reuse** its
  boot-after-RUNNING invariant — enforced **centrally by the supervisor** (§3.4), not re-implemented here.
- `EventBus.emit`/`bus.on`/`KNOWN_EVENTS`/`delivery_stats` are **shipped** (`core/events.py:100-152`,
  `events_catalogue.py:44`, verified). The relay delivers **through** the unchanged bus; `bus.emit` splats
  `handler(**payload)` (`events.py:116`, verified — the basis for the reserved-key contract §6.3).

**The genuinely undesigned gap this spec closes (all ⑥-owned):**

| Undesigned today | What this spec delivers |
|---|---|
| `EventSpec` has **no delivery field** (design-spec §2.8 EventSpec: `name/payload_schema/owner_subsystem/expected_subscribers/observability_only/audited/redaction_ref` — no durability). Every event is best-effort by omission. | **`EventSpec.delivery: DeliveryClass = BEST_EFFORT`** [S] — completes the frozen skeleton; `DeliveryClass` canonicalized in `sb/spec/events.py` so K7's `EventEmitSpec.delivery` imports **one** enum (seam-correction §12.1). |
| **No outbox table, no in-txn write, no relay** anywhere. `settings_mutation.py:385/400` and `xp_service.py:126` emit **after** commit (`pool.py:177` docstring: *"EventBus emission belongs AFTER this context exits (= after commit), never inside it"*). A crash in that window loses the audit-log embed and the reward announcement. | **`event_outbox` StoreSpec** + the in-txn `enqueue(conn, …)` primitive + the `OutboxRelayLane` poll cycle — the audit + reward paths become crash-durable. **Prerequisite:** the in-txn producers gain a conn-accepting form (§12.6). |
| The **exactly-once-relay vs handler-dedup contract under the dual-instance (merge=deploy fast-release) window** is unstated — it's the crux L-9/T2-3 leaves open. | The frozen three-part contract: **enqueue = exactly-once capture · relay→bus = at-least-once · effectful subscriber = idempotent on the dedup key** (§6). |
| The **relay-dedup application of the idempotency-key contract** (vocab §④.2 names it, doesn't shape it). | The outbox `dedup_key` **is** `IdempotencyKey.render()`; the `INSERT … ON CONFLICT (dedup_key) DO NOTHING` is the exactly-once capture guard (§5). The direct-lane token carries an event-name disambiguator so one mutation emitting ≥2 durable events never collides (§3.5). |

**Named canary:** `audit.action_recorded` — the smallest end-to-end durable event (already durable *row*,
lossy *delivery*). Its Gate-V oracle: enqueue in-txn → **kill the process before the relay ticks** →
restart → the server-log embed is delivered exactly once and no effectful subscriber double-fires (§6.5).
The reward twin canary is `economy.farm.collect`'s `xp.awarded` (shared with K7's farm-collect canary).

---

## 2. Files / modules it becomes

**New (`sb/kernel/outbox/`, layer = kernel; imports `utils`, `utils.db.*`, `sb/spec/events.py`,
`sb/kernel/db/idempotency`, `sb/kernel/scheduler/poll` (the `PollLane` port, from ⑦), `core.events`
(bus, for the relay leg only) — **never** cogs/views/services):**

| Path | Owns |
|---|---|
| `sb/spec/events.py` | **`DeliveryClass`** (canonical) + `EventSpec.delivery` [S] field. *Home of the `[S]` grammar; K7's local `DeliveryClass` copy re-homes here (§12.1).* |
| `sb/kernel/outbox/store.py` | `OutboxRow`, `OutboxStatus`, the `event_outbox` DDL + the conn-aware CRUD (`_insert`, `_claim`, `_mark_delivered`, `_mark_retry_or_dead`, `_prune`) — all via `utils.db.*` |
| `sb/kernel/outbox/enqueue.py` | `enqueue(conn, …) -> bool` · `enqueue_audit_action(conn, …) -> bool` · `enqueue_all(emits, ctx, result, *, conn) -> BestEffortBatch` (the K7 seam) · `BestEffortBatch.emit_after_commit()` |
| `sb/kernel/outbox/relay.py` | `OutboxRelayLane` (a `PollLane`) · `OutboxReaperLane` (a `PollLane`) · the `_deliver_cycle` body · `backoff(delivery_attempts)` · `MAX_ATTEMPTS` |
| `sb/kernel/outbox/metrics.py` | the four `MetricSpec`s (`outbox_pending_age_seconds`, `outbox_delivered_total`, `outbox_dead_letter_total`, `outbox_claims_total`) |

**Retired shipped paths** (commit-then-emit-outside-txn → in-txn enqueue):

| Shipped seam (verified) | How it changes |
|---|---|
| `services/settings_mutation.py:385` `emit_audit_action(...)` + `:400` `_emit_event(...)` (both **after** the `:338` `set_value_with_audit` txn commits at `:361`; ±line drift tolerable — both post-commit, verified) | For any `delivery=AT_LEAST_ONCE` event: the pipeline opens **one** `db.transaction()`, threads `conn` to the effect (via `set_value_with_audit`'s new conn-accepting form, §12.6) **and** to `enqueue_audit_action(conn,…)` + `enqueue(conn,…)`; best-effort events stay post-commit `bus.emit` |
| `services/xp_service.py:126` `bus.emit(EVT_XP_AWARDED)` + `:136` `bus.emit(EVT_LEVEL_UP)` (after `:124` `db.add_xp` commits internally, verified — `add_xp` owns its own txn, takes no external `conn`) | When `xp.awarded`/`xp.level_up` are declared `AT_LEAST_ONCE`, `add_xp` gains a conn-accepting form (§12.6); the mutation opens `db.transaction()` and the two emits become in-txn `enqueue(conn,…)` |
| `services/audit_events.py:89-93` the *"DB state is correct, event lost."* log line | Stays as the **best-effort** fallback path; for `AT_LEAST_ONCE` audited events the loss is structurally impossible (the row survives the crash) |
| `core/events.py` bus + `events_catalogue.py` | **Unchanged** — the relay emits through them; the catalogue name-guard is reused verbatim (`_check_catalogue`) |

---

## 3. The complete public contract

### 3.1 The delivery grammar — `sb/spec/events.py` (I complete the frozen skeleton)

```python
class DeliveryClass(enum.Enum):                 # CANONICAL home (K7 EventEmitSpec.delivery imports THIS — §12.1)
    BEST_EFFORT   = "best_effort"      # post-commit bus.emit; a drop is a log line (shipped default, Q-preserving)
    AT_LEAST_ONCE = "at_least_once"    # written as an event_outbox row INSIDE the txn; relay delivers post-commit

@dataclass(frozen=True)
class EventSpec:                                 # design-spec §2.8 — the frozen fields + the ONE new field
    name: str                                    # [S] legacy name verbatim, KNOWN_EVENTS-checked
    payload_schema: tuple[FieldSpec, ...]        # [S] superset of current kwargs (design-spec §2.8)
    owner_subsystem: str                         # [S]
    expected_subscribers: tuple[HandlerRef, ...] # [S]
    observability_only: bool = False             # [S]
    audited: bool = False                        # [S] this event carries an emit_audit_action fan-out (orthogonal to delivery)
    redaction_ref: RedactionRef | None = None    # [S]
    delivery: DeliveryClass = DeliveryClass.BEST_EFFORT   # [S] ← NEW. Completes the vocab §④/§⑤ skeleton.
```

- **No `AuditEventSpec` subclass.** A fully-durable audit path is just `EventSpec(audited=True,
  delivery=AT_LEAST_ONCE)` — the `audit.action_recorded` canary. (An earlier draft introduced an
  `AuditEventSpec(EventSpec)` with "audited=True enforced"; it had no consumer and no enforcement
  mechanism on a frozen dataclass, and the canary works via the plain fields — **dropped**, finding closed.)
- **`delivery` and `audited` are orthogonal.** `audited=True` = "this event IS an audit-row carrier"
  (design-spec §2.8, vocab §③.1). `delivery` = "how durably is it delivered." The recommended
  fully-durable audit path is `audited=True, delivery=AT_LEAST_ONCE`.
- **Compile fence (`delivery_declared`, additive to the manifest validator, §2 of design-spec §6
  `manifest-validate`):** ① `observability_only=True ⇒ delivery==BEST_EFFORT` (telemetry is never
  guaranteed-delivered); ② an `AT_LEAST_ONCE` event whose `owner_subsystem` writes no store the relay can
  reach is a `SEMANTIC_VIOLATION`; ③ an `AT_LEAST_ONCE` event whose `expected_subscribers` include an
  **effectful** handler requires that handler's signature to accept the reserved delivery keys (`**kwargs`
  or an explicit `_outbox_dedup_key` param) — the §6.3 dedup contract (verified for the canary: the
  shipped `_on_audit_action` already carries `**_extras`). Non-blocking for the v1 default (everything is
  BEST_EFFORT until opted in — the membership is owner-gated, §13 OD-1).

### 3.2 The row shape + status — `sb/kernel/outbox/store.py`

```python
class OutboxStatus(enum.Enum):
    PENDING   = "pending"     # awaiting (or retrying) delivery; claimable when available_at <= now
    DELIVERED = "delivered"   # relay confirmed publish-accepted; terminal
    DEAD      = "dead"        # exceeded MAX_ATTEMPTS delivery failures; terminal; an operator finding was recorded

@dataclass(frozen=True)
class OutboxRow:
    outbox_id: uuid.UUID
    dedup_key: str            # == IdempotencyKey.render(): f"{namespace}:{guild_id}:{dedup_token}" (vocab §④.1)
    event_name: str           # a KNOWN_EVENTS literal (checked at enqueue)
    payload: Mapping[str, object]     # JSON-native emit kwargs (payload_schema-shaped, JSONB; §6.5 codec)
    guild_id: int | None
    created_at: datetime      # enqueue time == the commit fact
    available_at: datetime    # earliest claim; bumped by the lease on claim, by backoff on retry
    claims: int               # leases TAKEN — incremented on every claim (crash-loop signal; does NOT gate DEAD)
    delivery_attempts: int    # bus-level delivery FAILURES — incremented ONLY on a step-3 relay-leg raise; MAX_ATTEMPTS gates THIS
    status: OutboxStatus
    delivered_at: datetime | None
    last_error: str | None
    correlation_id: uuid.UUID | None  # the producing mutation_id / audit_log row (vocab §③.2 link)
```

- **Two counters, deliberately separated (finding 6 closed).** `claims` counts leases taken; a relay that
  crashes or times out *mid-cycle* (§3.4 step 4) bumps `claims` on each re-claim but **never**
  `delivery_attempts`. `delivery_attempts` counts only **bus-level delivery failures** (§3.4 step 3), and
  `MAX_ATTEMPTS` gates DEAD on **it** — so a crash-looping/timing-out relay can **never** dead-letter a
  healthy event. A high `claims` with zero `delivery_attempts` and no DELIVERED transition is a **relay-health**
  signal (surfaced by `outbox_claims_total` + `outbox_pending_age_seconds`), an operator alert, not a silent drop.

### 3.3 The enqueue side (in-txn producers)

```python
# sb/kernel/outbox/enqueue.py
async def enqueue(
    conn: Connection, *,                 # the SAME txn-bound conn as once()/the effect (K3 db.transaction())
    event_name: str,                     # MUST be in KNOWN_EVENTS
    payload: Mapping[str, object],       # JSON-native (the codec §6.5 runs at the call boundary)
    guild_id: int | None,
    dedup_token: str,                    # the event's natural/derived token (see §3.5)
    namespace: str = "outbox",           # the IdempotencyKey namespace for the dedup_key render
    correlation_id: uuid.UUID | None = None,
) -> bool: ...                           # True = row inserted; False = ON CONFLICT (already captured — replay/dup)
#  Row init at insert (inside the caller's txn): outbox_id = uuid4(); created_at = available_at = clock.now()
#  (the row is immediately claimable once the txn commits); claims = 0; delivery_attempts = 0;
#  status = PENDING; delivered_at = None; last_error = None.
#  EventSpec lookup: enqueue resolves the spec by name from the compiled manifest registry
#  KNOWN_EVENTS: Mapping[str, EventSpec] (sb/spec/events.py, populated by the manifest build — the same
#  registry events_catalogue._check_catalogue reads) to run the deferral-3 payload key-presence check.

async def enqueue_audit_action(          # the DURABLE TWIN of the shipped emit_audit_action (§12.2; does NOT edit it)
    conn: Connection, *,
    mutation_id: str, subsystem: str, mutation_type: str, target: str, scope: str,
    guild_id: int | None, prev_value: str | None, new_value: str | None,
    actor_id: int | None, actor_type: str, occurred_at: datetime,
) -> bool: ...
# ↳ dedup_token = mutation_id (the frozen audit link, vocab §③.2); namespace="audit" (distinct from any
#   owner_subsystem — cannot collide even if a domain event on the same mutation shares mutation_id);
#   event_name = EVT_AUDIT_ACTION_RECORDED ("audit.action_recorded");
#   payload = the 11 fields with occurred_at SERIALIZED via .isoformat() (§6.5 — matching the shipped
#   bus payload audit_events.py:87 exactly, so the relayed event is byte-identical to what
#   server_logging._on_audit_action already receives); correlation_id = uuid(mutation_id).

async def enqueue_all(                   # the K7 seam (07-workflow-engine.md:192,236) — I own the body + return protocol
    emits: tuple[EventEmitSpec, ...], ctx: "WorkflowContext", result: "WorkflowResult", *,
    conn: Connection,                    # ← called IN-TXN (K7 step 4), never post-commit (§12.5)
) -> "BestEffortBatch": ...
# ↳ for each emit (emit_index = its position in `emits`):
#     delivery==AT_LEAST_ONCE ⇒ enqueue(conn, …) NOW (in-txn), dedup_token per §3.5;
#     delivery==BEST_EFFORT   ⇒ append (name, payload) to the returned batch.
#   `result` is the K7 DESIGN result type WorkflowResult (spec-only superset of the shipped
#   LifecycleResult:77 — no shipped `class WorkflowResult`; shared-vocab §0). `payload_builder(ctx, result)`
#   builds each emit payload.

@dataclass
class BestEffortBatch:
    _events: list[tuple[str, Mapping[str, object]]]
    async def emit_after_commit(self) -> int: ...   # bus.emit each, POST-commit; the K7 caller invokes this
                                                     # AFTER the txn exits (step 6). Dropping it = best-effort
                                                     # events never emit (the 07:192/236 bug — §12.5).
```

**The two-call protocol (finding 3 / §12.5 — pinned).** `enqueue_all` is a **single in-txn call at K7
step 4** that ① writes every `AT_LEAST_ONCE` row on `conn` immediately and ② *returns* a `BestEffortBatch`.
The K7 caller **captures that return** and, **after the `async with db.transaction()` block commits (step
6)**, calls `batch.emit_after_commit()`. It is **not** one call at step 6 (the conn is already committed
there — the in-txn row write would be impossible) and **not** a fire-and-drop (the best-effort events would
never emit). `07-workflow-engine.md:192,236` currently makes a single call and drops the return — **07 must
change** to this protocol (flagged §12.5).

- **Enqueue name-guard is HARD (fork D §8).** `enqueue`/`enqueue_audit_action` raise
  `UnknownEventError(name)` if `event_name ∉ KNOWN_EVENTS` — in-txn, so a mis-named guaranteed event
  **rolls back the whole effect** (delivery was promised; an undeliverable name is a bug caught at
  test/CI). BEST_EFFORT keeps the shipped **soft** behavior (one-shot WARNING + `unknown_event_total`,
  `events.py:_check_catalogue`), because a dropped telemetry name must never break a mutation.
- **`enqueue` is idempotent-by-key.** A `False` return (ON CONFLICT) means the event was already
  captured by a prior/concurrent txn — the caller treats it as success (no-op), never an error.

### 3.4 The relay side (post-commit delivery) — `sb/kernel/outbox/relay.py`

The relay is **not a standalone loop**. It is an `OutboxRelayLane` registered on the scheduler's shared
`PollSupervisor` (⑦, `09-scheduler-state.md` §3.6; 09 §8 closed "one PollSupervisor, registered lanes" over
"3 loops"). The supervisor owns the loop, the poll cadence, the readiness/drain gate, and per-lane
exception isolation; the lane owns *what one cycle does*.

```python
# sb/kernel/outbox/relay.py — imports sb/kernel/scheduler/poll.{PollLane, LaneTickResult} (owned by ⑦)
MAX_ATTEMPTS = 12    # gates DELIVERY_ATTEMPTS (bus-level failures) → DEAD + operator finding. NEVER gates claims.

def backoff(delivery_attempts: int, *, base_s: int = 5, cap_s: int = 300) -> int:  # min(base*2**(n-1), cap)
    ...

class OutboxRelayLane:                    # implements PollLane (⑦ §3.6)
    name = "outbox:relay"
    def __init__(self, *, bus, store, findings, batch_size: int = 100, lease_s: int = 30): ...
    async def tick(self, now: datetime) -> LaneTickResult: ...      # one claim→deliver cycle (table below)
    async def reconcile_on_boot(self, now: datetime) -> None:       # NO-OP (fork E): the first post-RUNNING
        return None                                                 # tick IS the reconcile — a normal claim
                                                                    # picks up every pre-crash PENDING row.

class OutboxReaperLane:                    # implements PollLane — the retention pruner (finding 11)
    name = "outbox:reaper"
    async def tick(self, now: datetime) -> LaneTickResult: ...      # store._prune(now, DELIVERED:7d, DEAD:90d), bounded
    async def reconcile_on_boot(self, now: datetime) -> None:
        return None
```

**Registration (composition root, at/after K5 — where ⑦ spawns the supervisor):**

```python
supervisor.register_lane(OutboxRelayLane(bus=bus, store=outbox_store, findings=findings))
supervisor.register_lane(OutboxReaperLane(store=outbox_store))
# The scheduler's PollSupervisor.run_forever(poll_interval_s=5) drives both lanes' tick(now).
```

**`OutboxRelayLane.tick(now)` fixed cycle (buildable, zero further decisions):**

| # | Step | Rule / failure mode |
|---|---|---|
| 0 | **readiness gate — SUPERVISOR-OWNED, not re-implemented here** | The lane does **no** step-0 gate of its own. The supervisor performs **no** lane work — neither `reconcile_on_boot` nor `tick` — until lifecycle **RUNNING** (09 §3.6, vocab §⑤.5), and skips claiming on **DRAINING** (`can_accept_commands()` false). Because ticking begins only *after* RUNNING and both `is_running()` and `can_accept_commands()` exclude DRAINING, the outbox's earlier "RUNNING-only, NOT can_accept_commands" distinction collapses for this lane: the only window where the two predicates differ (STARTING) never sees an outbox claim. **The invariant "never poll a DB the `/ready` gate would 503" holds by the supervisor's gating** (vocab §⑤.3). |
| 1 | **atomic claim** | one statement (§5.2): select `PENDING` rows with `available_at <= now` `ORDER BY available_at, outbox_id LIMIT batch_size FOR UPDATE SKIP LOCKED`, `SET claims = claims + 1, available_at = now + lease_s`, `RETURNING *`. **`SKIP LOCKED` = the dual-instance guard** (each row claimed by exactly one poller per cycle). `outbox_claims_total.inc(n)`. |
| 2 | **deliver each** | `await bus.emit(row.event_name, **row.payload, _outbox_dedup_key=row.dedup_key, _outbox_correlation_id=row.correlation_id)` — publish-accepted (shipped semantics; a subscriber failure never raises). On return ⇒ `_mark_delivered(row.outbox_id, now)` (`status=DELIVERED, delivered_at=now`); `outbox_delivered_total.inc()`. The two reserved `_outbox_*` kwargs are the §6.3 dedup carriers. |
| 3 | **relay-leg failure** | if `bus.emit` **itself** raises (bus-level, not subscriber-level — rare): `_mark_retry_or_dead`: `delivery_attempts + 1 >= MAX_ATTEMPTS ⇒ status=DEAD` + `record_operator_finding(...)` (§4 Consumes) + `outbox_dead_letter_total.inc()`; else `status=PENDING, delivery_attempts = delivery_attempts + 1, available_at = now + backoff(delivery_attempts), last_error=str(exc)`. **Only this step touches `delivery_attempts`.** |
| 4 | **crash / timeout mid-cycle** | a row claimed (lease bumped, `claims++`) but neither delivered nor retried before a crash reappears as claimable when its lease lapses (`available_at <= now` again) → **re-emitted (at-least-once)**, `claims++` again but `delivery_attempts` **unchanged**. No 'claimed' status needed; the lease IS the visibility timeout. A lane exception that escapes `tick` is caught+logged by the supervisor (per-lane isolation, 09 §3.6); it is **not** recorded as a per-poll finding (the PollLane model has no per-lane `error_policy` — §12.4). |
| 5 | **return** | `LaneTickResult(lane="outbox:relay", claimed=n, fired=delivered, failed=retried+dead_lettered, skipped=0)` (the field mapping onto ⑦'s shape). |

- **Ordering.** Best-effort FIFO per guild via `ORDER BY available_at, outbox_id`; strict cross-event
  ordering is a **deferral** (§9) — subscribers must not assume it (matches the shipped fire-and-forget
  bus, which has none). `xp.awarded` before `xp.level_up` is preserved *within one txn* by insertion order
  + created_at tiebreak, not guaranteed across txns.

### 3.5 The dedup-token derivation (the relay-dedup key — vocab §④.2 completion)

The outbox `dedup_key = IdempotencyKey(namespace, guild_id, dedup_token).render()`. The per-producer
`dedup_token` **always carries an event disambiguator** so one mutation emitting ≥2 durable events yields
≥2 distinct keys (finding 2 closed):

| Producer | `namespace` | `dedup_token` | Capture guarantee |
|---|---|---|---|
| **K7 workflow event** (`enqueue_all`), op is `DURABLE_ONCE` | `op_key` | `f"{op.dedup_key.render(ctx)}:{emit_index}"` — shares the op's `once()` key | **exactly-once**: a replay hits `once()`=False and never re-enters enqueue (farm-collect's `xp.awarded` fires once across deploy overlap) |
| **K7 workflow event**, op is `NATURAL_KEY`/`SINGLE_FLIGHT` | `op_key` | `f"{mutation_id}:{emit_index}"` (fresh per real invocation) | exactly-once **capture** (fresh id + in-txn); a duplicate from two *distinct* invocations is absorbed by handler-dedup |
| **Direct-lane audit** (`enqueue_audit_action`) | `"audit"` | `mutation_id` (the frozen audit link; exactly one audit event per mutation) | **exactly-once**: one mutation → one `mutation_id` → one row. Distinct namespace from any domain event, so no cross-collision even sharing `mutation_id`. |
| **Direct-lane domain event** (e.g. settings `governance.*.changed`) | `owner_subsystem` | `f"{mutation_id}:{event_name}"` ← **event-name disambiguator** | exactly-once capture; **two distinct events from one mutation get distinct keys** (without the suffix the 2nd would `ON CONFLICT`-drop — the collision this closes) |

Because the row is inserted on the **same conn** as `once()` + the effect, the event exists **iff** the
effect committed — no phantom events (rolled-back effect ⇒ no row) and no lost events (committed effect ⇒
row present, relay eventually delivers).

### 3.6 Failure-mode catalogue

| Mode | Behavior |
|---|---|
| Effect txn rolls back | The outbox row is in the same txn → also rolled back. No event. Correct. |
| Process dies after commit, before relay | Row persists as PENDING; the relay's first post-boot (post-RUNNING) tick delivers it. **The L-9 window is closed.** |
| One mutation emits ≥2 `AT_LEAST_ONCE` domain events | each carries a distinct `:{event_name}` suffix (direct lane) / `:{emit_index}` (K7 lane) → distinct `dedup_key` → **both captured**. (Without the suffix the 2nd would silently `ON CONFLICT`-drop — the finding-2 collision.) |
| `bus.emit` raises (bus-level) | Retry with backoff on `delivery_attempts`; DEAD + operator finding after `MAX_ATTEMPTS` **delivery failures**. |
| Relay crashes/times out mid-cycle repeatedly | `claims` climbs, `delivery_attempts` stays 0 → the healthy event is **never** dead-lettered; surfaced as a relay-health alert (`outbox_claims_total` high, `outbox_pending_age_seconds` growing). |
| Subscriber raises/times out | Isolated by the shipped bus (`events.py:114-137`) — the row is still marked DELIVERED (publish-accepted). Effectful subscribers must self-dedup (§6.3); this is why delivery ≠ subscriber-success. |
| Two instances poll concurrently | `FOR UPDATE SKIP LOCKED` → disjoint claims per cycle; a lapsed lease can cause one duplicate emit → handler-dedup absorbs it. |
| Duplicate gateway delivery (deploy overlap) enqueues twice | `ON CONFLICT (dedup_key) DO NOTHING` → one row → one delivery. |
| Unknown event name, `AT_LEAST_ONCE` | `UnknownEventError` in-txn → effect rolls back (loud, dev-caught). |
| Unknown event name, `BEST_EFFORT` | Shipped soft-warn + metric; mutation proceeds. |

---

## 4. Provides / Consumes

**Provides (owned canonical shapes others consume):**

| Shape | Consumer |
|---|---|
| `DeliveryClass` + `EventSpec.delivery` [S] | every manifest author; K7's `EventEmitSpec.delivery` (imports this enum — §12.1); the `delivery_declared` compile fence |
| `enqueue(conn,…)` / `enqueue_audit_action(conn,…)` | every `*_mutation.py` on the direct lane (settings, governance, role, moderation, …) that opts an event into `AT_LEAST_ONCE` (via the §12.6 conn-accepting form) |
| `enqueue_all(emits, ctx, result, *, conn) -> BestEffortBatch` | **K7 workflow engine** (`07-workflow-engine.md:192,236`) — its `run()` **step-4 in-txn call**; the returned `BestEffortBatch.emit_after_commit()` at **step 6, post-commit** (§3.3, §12.5) |
| `OutboxRelayLane` / `OutboxReaperLane` (both `PollLane`) + the `event_outbox` StoreSpec | the composition root (registers them on ⑦'s `PollSupervisor`); the operator dashboard (a read-only projection of pending/dead rows) |
| the **exactly-once-capture / at-least-once-relay / handler-dedup** contract (§6) + the reserved `_outbox_dedup_key`/`_outbox_correlation_id` delivery keys | every effectful subscriber (must self-dedup on `_outbox_dedup_key`); every observability subscriber (tolerates dup, ignores the reserved keys via `**kwargs`) |

**Consumes (assumed sibling shapes — exact assumption stated):**

| Shape | Owner | Exact assumed contract |
|---|---|---|
| `db.transaction()` → txn-bound `conn` | **K3 / spec 05** | `async with db.transaction() as conn:` yields a `conn.transaction()`-bound Connection (verified `pool.py:170-182`); the enqueue INSERT rides this conn |
| `IdempotencyKey(namespace, guild_id, dedup_token).render()` + `once`/`read_outcome` | **K3 / spec 05** | `render() == f"{namespace}:{guild_id}:{dedup_token}"` (vocab §④.1); the outbox `dedup_key` **is** this string; enqueue never re-enters on a replay because K7's `once()` already gated the txn body |
| `PollSupervisor` / `PollLane` / `LaneTickResult` | **scheduler ⑦ / spec 09 (§3.6)** | `PollLane.tick(now)->LaneTickResult` + `reconcile_on_boot(now)->None`; `register_lane(lane)`; `run_forever(poll_interval_s=5)`; supervisor gates on RUNNING (first) / `can_accept_commands()` (per tick) + per-lane exception isolation. **I register `OutboxRelayLane`/`OutboxReaperLane`; I do not own the loop.** |
| `emit_audit_action(**11 fields) -> bool` + `EVT_AUDIT_ACTION_RECORDED` | **shipped `audit_events.py:52`** | the 11-field payload + the `"audit.action_recorded"` literal are frozen (vocab §③.2); `occurred_at` rides the bus as `.isoformat()` (`:87`); the subscriber `_on_audit_action(occurred_at: str, …, **_extras)` (verified `server_logging.py:773-787`) types it `str` and tolerates the reserved keys via `**_extras`; `enqueue_audit_action` carries them identically |
| `bus.emit(name, **payload)` / `KNOWN_EVENTS` / `_check_catalogue` | **shipped `core/events.py:100`, `events_catalogue.py:44`** | publish-accepted (a subscriber failure never raises); `bus.emit` splats `handler(**payload)` (`:116`) — the basis for the reserved-key delivery contract; the relay treats a normal return as delivered |
| `record_operator_finding(*, source, severity, summary, detail, correlation_id) -> None` | **the diagnostics/findings engine (control plane; NOT yet frozen in any strand-2 spec)** | **Consumes-assumption, exact assumed shape stated here.** A DEAD row records one persistent finding through the **same seam the scheduler's `ErrorPolicy.ESCALATE_FINDING` invokes** (09 §3.8). If the findings engine lands a different signature, this call adapts — one call site, `sb.kernel.outbox` as `source`. *(The earlier "design-spec §2.8 DiagnosticProviderSpec / mig-057 semantics" attribution was unverifiable — `mig-057` appears nowhere in the corpus, and DiagnosticProviderSpec defines no such function — and is **removed**.)* |
| `WorkflowContext` / `WorkflowResult` / `EventEmitSpec` | **K7 / spec 07** | `enqueue_all` reads `emit.delivery`, `emit.event`, `emit.payload_builder(ctx, result)` (`07:114-119`) and `ctx.guild_id`. `WorkflowResult` is the **K7 design result type** (spec-only superset of the shipped `LifecycleResult` — no shipped `class WorkflowResult`; shared-vocab §0). |

---

## 5. Data model + migration / index shape

### 5.1 The `event_outbox` table (owned; StoreSpec, K4 band)

```
event_outbox (
  outbox_id          uuid        PRIMARY KEY,               -- the row's own id
  dedup_key          text        NOT NULL,                  -- IdempotencyKey.render() — the exactly-once capture key
  event_name         text        NOT NULL,                  -- a KNOWN_EVENTS literal
  payload            jsonb       NOT NULL,                  -- JSON-native emit kwargs (§6.5 codec)
  guild_id           bigint      NULL,
  created_at         timestamptz NOT NULL,                  -- == the commit fact
  available_at       timestamptz NOT NULL,                  -- claim/lease/backoff cursor
  claims             int         NOT NULL DEFAULT 0,        -- leases taken (crash-loop signal; does NOT gate DEAD)
  delivery_attempts  int         NOT NULL DEFAULT 0,        -- bus-level delivery failures; MAX_ATTEMPTS gates DEAD on THIS
  status             text        NOT NULL DEFAULT 'pending', -- 'pending' | 'delivered' | 'dead'
  delivered_at       timestamptz NULL,
  last_error         text        NULL,
  correlation_id     uuid        NULL                        -- the producing mutation_id / audit_log row
)
```

Indexes:
- **`UNIQUE (dedup_key)`** — the exactly-once capture guard (`INSERT … ON CONFLICT (dedup_key) DO NOTHING`).
  This is the *relay-dedup application of the idempotency-key contract* (vocab §④.2).
- **`(available_at) WHERE status = 'pending'`** (partial) — the relay claim/due poll (small and hot).
- **`(status, delivered_at) WHERE status IN ('delivered','dead')`** (partial) — the `OutboxReaperLane` prune scan.
- `(correlation_id) WHERE correlation_id IS NOT NULL` — trace an event back to its `audit_log` row.

```python
OUTBOX_STORE = StoreSpec(                        # the version-extended StoreSpec (⑦ §3.2, sb/spec/versioning.py)
    table="event_outbox",
    sole_writer=EngineRef("sb.kernel.outbox"),   # only the outbox engine writes it (INV-style sole-writer)
    retention="delivered:7d;dead:90d",           # enforced by OutboxReaperLane._prune (below); NOT unowned
    checkpoint_class=CheckpointClass.LEDGER,      # the ENUM (⑦ §3.2), not the string "ledger" (seam-correction)
    invariant_tag="INV-OUTBOX-SOLE-WRITER",      # namespace-reserved; generates the AST fence
    reader_domains=("operator_dashboard",),      # read-only projection; never a second write path
    # ---- version-extended fields (⑦ §3.2). The outbox is a SELF-MANAGED delivery ledger: ----
    payload_version=1,
    bears_value=False,                           # the row is a delivery ENVELOPE; the money/state of record
                                                 # already committed to its DOMAIN table in the same txn.
                                                 # Losing an undelivered row loses a delivery, never value.
    version_policy=VersionPolicy.REJECT_AND_PRESERVE,  # non-destructive default; NO compensation_ref needed
                                                       # (bears_value=False). See exemption note below.
)
```

- **Exemption from `resolve_versioned_load` / `run_recovery` (finding: CheckpointClass enum + version
  fields).** The version-restore machinery (⑦ §3.3) is for SESSION/AGGREGATE stores a cog *restores into a
  live domain*. The outbox is a **LEDGER with an explicit `PENDING/DELIVERED/DEAD` lifecycle** the relay
  drives — it **does not route through `resolve_versioned_load`**. The version fields are declared to (a)
  satisfy the version-extended `StoreSpec` grammar + the `value_bearing_store_cannot_drop` fence and (b)
  record the payload schema version. `version_policy=REJECT_AND_PRESERVE` is chosen because it is
  **non-destructive** — `DROP` would strand (lose) a still-`PENDING` row on a schema bump, violating "no
  lost events." A schema-drifted PENDING row is simply **re-emitted as-stored**: `payload_schema` evolves
  **additive-only** (deferral 3 + the manifest superset rule), so an old-shape payload is always a valid
  subset. This is why `bears_value=False` + `REJECT_AND_PRESERVE` is correct here even though the row never
  reaches the compensation path.
- **Retention pruner (finding 11).** `OutboxReaperLane._prune(now)` runs a **bounded** `DELETE FROM
  event_outbox WHERE (status='delivered' AND delivered_at < now - INTERVAL '7 days') OR (status='dead' AND
  created_at < now - INTERVAL '90 days') LIMIT $batch` each tick (via `utils.db.outbox`). Owner:
  `sb.kernel.outbox` (the sole writer). Registered on ⑦'s `PollSupervisor` alongside the relay lane.

### 5.2 The atomic claim statement (dual-instance safe)

```sql
WITH due AS (
  SELECT outbox_id FROM event_outbox
   WHERE status = 'pending' AND available_at <= $now
   ORDER BY available_at, outbox_id
   LIMIT $batch
   FOR UPDATE SKIP LOCKED
)
UPDATE event_outbox o
   SET claims = o.claims + 1, available_at = $now + $lease
  FROM due WHERE o.outbox_id = due.outbox_id
RETURNING o.*;
```

Note the claim increments **`claims`**, never `delivery_attempts` (finding 6). `delivery_attempts` moves
**only** on a step-3 bus-level failure. All access is via `utils.db.*` conn-aware primitives (a new
`utils/db/outbox.py` submodule) — **never** raw `conn.execute` outside `utils/db/` (arch rule §7).

**Migration:** `000N_event_outbox.sql` creates the table + 4 indexes in the K4 band. Fresh chain (design-spec
§5.2 decision 8); no legacy table to import (the outbox is net-new).

---

## 6. Restart & merge=deploy behavior — the exactly-once contract

This is the crux the task flags. **End-to-end exactly-once *to a subscriber* is impossible** with a
fire-and-forget in-process bus (the relay cannot atomically both `bus.emit` — a side effect outside the
DB — and mark the row delivered in one commit). So the frozen contract is a **three-part split**:

### 6.1 Enqueue = exactly-once capture
The row is written in-txn under `UNIQUE(dedup_key)`. The event exists **iff** the effect committed
(rolled-back effect ⇒ no row; committed effect ⇒ exactly one row; a duplicate enqueue ⇒ `ON CONFLICT`
no-op). One mutation emitting ≥2 durable events yields ≥2 distinct keys (§3.5 disambiguator). **No phantom
events, no lost events.**

### 6.2 Relay → bus = at-least-once
A crash between `bus.emit` and `_mark_delivered` leaves the row PENDING (its lease lapses) → it is
re-emitted next cycle. So a subscriber may be invoked **≥ 1** times.

### 6.3 Effectful subscriber = idempotent on the dedup key
The relay carries the capture key on the delivered emit as the **reserved kwarg `_outbox_dedup_key`** (and
the `audit_log` link as `_outbox_correlation_id`). Because `bus.emit` splats `handler(**payload)`
(`events.py:116`, verified), these arrive as extra keyword arguments:
- **Effectful subscribers** (a reward accrual, a second durable write) MUST dedup: their handler signature
  **accepts the reserved keys** (declare `**kwargs`, or an explicit `_outbox_dedup_key: str` param) and
  guards its own effect with `once(IdempotencyKey.parse(_outbox_dedup_key))` inside its own
  `db.transaction()`. A redelivery then no-ops. **This is enforced by the `delivery_declared` fence ③**
  (§3.1) — an `AT_LEAST_ONCE` event with an effectful subscriber that can't receive the reserved keys is a
  `SEMANTIC_VIOLATION`.
- **Observability subscribers** (server-log embeds, metrics) tolerate duplicates and need no dedup; they
  **ignore** the reserved keys via `**kwargs`. The **shipped canary subscriber already does this** —
  `_on_audit_action(…, occurred_at: str, **_extras)` (verified `server_logging.py:786`) absorbs the two
  `_outbox_*` keys into `**_extras` and renders the **identical** embed. So "the subscriber is untouched /
  receives the identical named event" and "the relay carries `_outbox_dedup_key`" are **both true and
  reconciled**: the named payload_schema fields are byte-identical; the two reserved keys ride *alongside*
  (never inside the frozen `payload_schema`), read only by subscribers that opt in.

### 6.4 Dual-instance overlap (fast-release / merge=deploy window)
Two workers may both run the relay lane's tick. `FOR UPDATE SKIP LOCKED` + the visibility lease means each
PENDING row is claimed by **exactly one** poller per cycle; the sub-second both-live window can at most let
a lease lapse and the other instance re-claim → **one** duplicate emit → absorbed by §6.3 handler-dedup.
This is the **same** `once()`+`db.transaction()` uniform coverage that makes fast-release *correct* where
the `#1693` listener-only gate was not (vocab §⑤.4). **Consequences:** the relay needs **no drain-to-zero**
and **no separate boot-reconcile** — *the first post-`/ready`-200 (post-RUNNING) tick IS the reconcile* (it
picks up every PENDING row, including those enqueued-but-never-delivered before the crash). The only restart
invariant — start delivering **after RUNNING** — is enforced **by the supervisor's central gate** (§3.4
step 0), not by a lane-local predicate.

### 6.5 The payload codec (JSONB serialize / re-emit contract)
`payload` is JSONB and cannot hold a `datetime`/enum/`uuid` natively, so the emit kwargs are serialized to
**JSON-native** values at the `enqueue` boundary and re-emitted with the types each event's **shipped bus
contract** expects:

| Typed field | Stored in JSONB as | Re-emitted by the relay as |
|---|---|---|
| `datetime` | `.isoformat()` string | the **string** (matching the shipped payload — e.g. `audit.action_recorded.occurred_at` is `.isoformat()` on the bus, `audit_events.py:87`; `_on_audit_action` types it `str`) |
| `enum` | `.value` | its `.value` (the shipped events pass value strings) |
| `uuid.UUID` | `str(u)` | `str` |
| `int` / `str` / `bool` / `None` / nested `dict`/`list` of these | verbatim | verbatim |

So the audit twin stores the 11 fields with `occurred_at` **already** an ISO string and the relay emits it
unchanged — the delivered event is **byte-identical** to what `server_logging._on_audit_action` receives
today. **"Verbatim" holds only where no transform is needed;** typed fields go through this codec. A general
`to_jsonable(payload_schema, kwargs)` / `from_jsonable` pair (keyed by each `FieldSpec`'s declared type)
lives in `sb/kernel/outbox/enqueue.py`; the relay applies the inverse only where a shipped subscriber
expects a non-string type (audit needs none — its bus payload is already all-JSON-native).

### 6.6 The canary's failure arm (FJ §4 item 15)
`audit.action_recorded`: enqueue in-txn → `kill -9` before the relay ticks → restart → assert (a) the
server-log embed is delivered, (b) exactly one `audit_log`-linked embed exists (no duplicate), (c) no
effectful subscriber double-fired. This is the Gate-V acceptance oracle for the whole outbox.

---

## 7. Architecture rules honored (INV / layer cites)

- **Layer.** `sb/kernel/outbox/` (kernel) imports `utils`, `utils.db.*`, `sb/spec/events.py`,
  `sb/kernel/db/idempotency`, `sb/kernel/scheduler/poll` (the `PollLane` port), and `core.events` (bus —
  the relay leg only) — **never `cogs/` or `views/`** (services→views zero-tolerance honored; CLAUDE.md
  layer table). Enqueue is called *down* by domain `*_mutation.py` (services→kernel, allowed) and by K7.
- **All DB via `utils.db.*`.** A new `utils/db/outbox.py` submodule owns every `event_outbox` statement
  (claim, mark, prune); no raw `pool.execute`/`conn.execute` outside `utils/db/` (the same rule the shipped
  `pool.py` seam obeys).
- **All mutations through the domain `*_mutation.py` seam.** The outbox does not mutate domain state — it
  records a *delivery intent* alongside the mutation, on the mutation's own conn. Enqueue is never a second
  write path to a domain table.
- **All auditable mutations call `emit_audit_action`.** Preserved: `enqueue_audit_action` carries the
  identical 11-field payload and the relay delivers the identical `audit.action_recorded` event — the
  audited seam is *strengthened* (durable), never bypassed (vocab §③.2).
- **Settings via `settings_keys` constants** — the retired `settings_mutation` path keeps its constants;
  only the emit *timing* moves in-txn (via the §12.6 conn-accepting form).
- **INV — sole writer.** `event_outbox` is written **only** by `sb.kernel.outbox` (`OUTBOX_STORE.sole_writer`
  + `INV-OUTBOX-SOLE-WRITER` AST fence). The dashboard is `reader_domains` only.
- **Namespace.** `outbox:relay` / `outbox:reaper` lane names are `task_prefix`-kind (namespace-reserved);
  `audit`/`outbox`/`<owner_subsystem>` dedup namespaces are reserved so no domain re-uses them.

---

## 8. Options → Decision → Why (per fork closed)

| Fork | Options | **Decision** | Why |
|---|---|---|---|
| **A · delivery tiers (T2-3)** | (i) everything at-least-once (ii) everything best-effort (shipped) (iii) per-`EventSpec` declared, default best-effort | **(iii) `EventSpec.delivery` per event, default `BEST_EFFORT`; audit + reward opt into `AT_LEAST_ONCE`** | T2-3 recommendation verbatim. Default-best-effort = zero behavior change for the 30+ observability-only events. *Which* events opt in is owner-gated (§13 OD-1). |
| **B · exactly-once posture** | (i) promise end-to-end exactly-once (ii) exactly-once *capture* + at-least-once *relay* + handler-dedup (iii) at-most-once | **(ii)** | (i) is impossible over a fire-and-forget bus without 2PC; (iii) loses events. (ii) is the standard transactional-outbox contract and composes with K3's `once()` exactly (§6). |
| **C · relay claim under dual-instance** | (i) single-relay leader lock (ii) `FOR UPDATE SKIP LOCKED` + visibility lease (iii) advisory lock per row | **(ii)** | Matches fast-release (no leader election, no drain); the scheduler ⑦ uses the same pattern; handler-dedup is the backstop for the rare lease-lapse duplicate (vocab §⑤.4). |
| **D · unknown-name at enqueue** | (i) soft-warn like the shipped bus (ii) hard-raise in-txn for `AT_LEAST_ONCE` (iii) drop silently | **(ii) hard-raise for `AT_LEAST_ONCE`; keep soft-warn for `BEST_EFFORT`** | A guaranteed event that can't deliver is a bug that should fail the effect loudly (dev/CI-caught); a telemetry name must never break a mutation (shipped honesty preserved). |
| **E · boot-reconcile** | (i) a dedicated boot sweep (ii) the first post-ready tick IS the reconcile | **(ii)** | The relay's normal claim already selects every PENDING row; a separate sweep is redundant. `reconcile_on_boot` is a no-op; the supervisor's post-RUNNING gate is the only invariant (§6.4). |
| **F · `DeliveryClass` home** | (i) K7's `sb/kernel/workflow/spec.py` (as spec 07 drafted) (ii) `sb/spec/events.py` next to `EventSpec` | **(ii)** | `EventSpec.delivery` and `EventEmitSpec.delivery` must share ONE enum or they drift (the RC-3 Lane lesson). `EventSpec` is the manifest owner; the leaf is the lowest common home. §12.1 reconciles. |
| **G · relay topology** | (i) a standalone `RELAY_TASK` `ManagedTaskSpec` + own `Interval(1s)` loop wired by the composition root (this doc's earlier draft) (ii) an `OutboxRelayLane` (`PollLane`) on the scheduler's shared `PollSupervisor` | **(ii)** | **The scheduler ⑦ owns the poll infrastructure and already closed this** (09 §8 "one PollSupervisor, registered lanes" over "3 loops"). One loop = one lifecycle/drain gate, one supervised task, per-lane isolation. Adopting the port removes the two-model contradiction (§12.4); delivery latency ≤ the supervisor's 5s cadence — acceptable for audit/reward (a tighter per-lane cadence is a bounded tuning knob, §9). |

---

## 9. Labeled deferrals (each bounded)

1. **Strict cross-event ordering.** v1 = best-effort FIFO per guild (`ORDER BY available_at, outbox_id`).
   A per-(guild, stream) sequence guarantee is deferred — no shipped subscriber assumes ordering (the bus
   has none). Bounded: add a `sequence` column + per-stream serial claim when a subscriber needs it.
2. **Delivery-latency cadence.** The relay ticks at the supervisor's `poll_interval_s=5`, so worst-case
   delivery latency is ~5s — fine for audit-log embeds and reward announcements. A tighter dedicated
   cadence (a faster sub-lane, or an event-nudge that wakes the supervisor on enqueue) is a bounded tuning
   knob; the lane contract is unchanged. **Not owner-gated** (a perf tune, not a policy).
3. **Payload schema enforcement at enqueue.** v1 validates the event *name* (KNOWN_EVENTS) + key-presence
   against `payload_schema` (resolving the `EventSpec` from the manifest `KNOWN_EVENTS` registry, §3.3);
   full type-validation at enqueue is deferred to the compile-time superset check (design-spec §2.8).
   `payload_schema` evolves **additive-only** (the manifest superset rule) — the invariant the outbox's
   re-emit-as-stored posture (§5.1) relies on. Bounded — a `validate_payload(spec, payload)` hook slot exists.
4. **Cross-process bus (Redis pub/sub).** The relay stays in-process (ADR-001 single-process, vocab / T2-13).
   `events.py`'s own "future sharding note" is the seam; the outbox table is already the durable substrate a
   sharded relay would read.
5. **Dead-letter replay UI.** DEAD rows are retained 90d + record a finding; an operator "replay this dead
   event" action is deferred to the dashboard band. The row + `correlation_id` are the forward seam.

All deferrals sit behind a designed seam; none blocks building the outbox + the audit canary now.

---

## 10. Retirement map (FJ L-rows / §4 gaps / owner-queue)

| Row | How this spec retires it |
|---|---|
| **L-9 — no outbox / at-least-once anywhere; commit-then-emit outside txn; "event lost" is a log line** | The `event_outbox` table + in-txn `enqueue`/`enqueue_audit_action` + the `OutboxRelayLane` claim/deliver cycle make audit + reward crash-durable; `settings_mutation.py:385/400` and `xp_service.py:126/136` move in-txn (via the §12.6 conn-accepting form); `audit_events.py:89-93` loss becomes structurally impossible for `AT_LEAST_ONCE`. **CLAIMED / CLOSED.** |
| **T2-3 — internal event durability: outbox / at-least-once tiers** | `EventSpec.delivery{BEST_EFFORT, AT_LEAST_ONCE}` + the in-txn outbox, default best-effort, audit+reward opt-in (§8 fork A). **CLAIMED / CLOSED** (exact membership → §13 OD-1, owner-gated). |
| **§④.2 row 3 vocab skeleton — "Leg / relay dedup: the outbox row is written inside the same `db.transaction()` conn as `once()`"** | The outbox `dedup_key = IdempotencyKey.render()`; the `ON CONFLICT` guard is the relay-dedup application of the idempotency-key contract (§3.5, §5.1). **COMPLETED.** *(Prior draft mislabeled this "§③.4 vocab skeleton" — §③.4 is the audit-completeness fence; the outbox skeleton lives in §④.2 row 3. Label corrected.)* |
| **§⑤.2 vocab skeleton — "the outbox's at-least-once delivery" (restart-safety)** | The relay's post-`/ready`-200 tick IS the boot-reconcile; `FOR UPDATE SKIP LOCKED` + lease covers the fast-release window (§6.4); the supervisor's RUNNING gate is the boot-order invariant. **COMPLETED.** |
| **L-6 — deploy-overlap double-fire (event-delivery leg)** | A gateway event delivered to both instances enqueues once (`ON CONFLICT`) and delivers once + handler-dedup; the outbox closes the **event-delivery** lane. **PARTIAL — event-delivery leg CLOSED; the command-dispatch leg is the resolver's dedup checkpoint (vocab §④.2), co-owned.** |
| **FJ §4 item 15 — named canaries have no failure arm (durability leg)** | `audit.action_recorded`'s kill-before-relay oracle (§6.6) is the outbox canary's pass/fail. **PARTIAL — outbox durability canary CLOSED; shares K7's farm-collect `xp.awarded` arm.** |
| **T2-2 — fast-release + durable per-action idempotency (event-delivery half)** | The outbox is the event-lane realization of fast-release: no drain, `once()`-uniform, overlap-safe (§6.4). **CO-OWNED with the resolver/K7 dispatch-dedup; event-delivery half provided.** |

---

## 11. Build order (K0-K10 placement + what it blocks)

**Placement:** **K4 — the events band** (design-spec §11 dependency chain: K1 namespace, K2 grammar/refs,
K3 db+idempotency, **K4 events**, K5 lifecycle, K6 authority, K7 workflow). The enqueue/store/spec depend
only on K3 (`db.transaction()`, `IdempotencyKey`) + `sb/spec/events.py`. The **relay lane registration**
depends on ⑦'s `PollSupervisor`, which the scheduler spawns under **K5** — so the lane is *registered* at/after
K5, though it is *authored* in the K4 band.

**Sub-order within K4 (each lands with its checker):**
1. `sb/spec/events.py` — `DeliveryClass` + `EventSpec.delivery` [S] + the `delivery_declared` compile fence
   (tests: `observability_only ⇒ BEST_EFFORT`; effectful-subscriber-needs-reserved-keys).
2. `sb/kernel/outbox/store.py` + `utils/db/outbox.py` + `000N_event_outbox.sql` — table, 4 indexes,
   conn-aware CRUD (`_insert`/`_claim`/`_mark_*`/`_prune`), the atomic claim (§5.2), `OUTBOX_STORE`.
3. `sb/kernel/outbox/enqueue.py` — `enqueue` / `enqueue_audit_action` / `enqueue_all` / `BestEffortBatch`
   + the JSONB codec (§6.5) over K3 `db.transaction()`.
4. `sb/kernel/outbox/relay.py` + `metrics.py` — `OutboxRelayLane` / `OutboxReaperLane` (`PollLane`s),
   `backoff`, `MAX_ATTEMPTS`; **register both on ⑦'s `PollSupervisor` in the composition root at/after K5**.
5. **canary:** make `audit.action_recorded` `AT_LEAST_ONCE`; write the kill-before-relay oracle (§6.6).

**What ⑥ blocks / unblocks:**
- **K7 workflow engine** — its `run()` **step-4 in-txn** `outbox.enqueue_all(…, conn=conn)` + **step-6
  post-commit** `batch.emit_after_commit()` need this seam (§3.3); spec 07's §4 "v1 fallback: a thin
  implementation that `bus.emit`s after commit" is **replaced by this durable implementation** — but 07's
  **single-call/step-6 text must change** to the two-call protocol or best-effort events never emit (§12.5).
- **The scheduler ⑦** — provides the `PollSupervisor` the relay lane rides; peers via the shared K3 substrate.
- **The durable audit + reward paths** — `settings_mutation`, `xp_service`, `economy_service`, and every
  `audited=True, delivery=AT_LEAST_ONCE` event (each needs the §12.6 conn-accepting form to move in-txn).
- **The operator dashboard** — a read-only pending/dead projection (design-spec §6 control plane; never a
  second write path).

---

## 12. Seam corrections (flagged; source-wins Q-0120)

1. **`DeliveryClass` canonical home (reconciles K7 spec 07 §3.1).** `07-workflow-engine.md:99-102` declares
   `class DeliveryClass(enum.Enum)` inside `sb/kernel/workflow/spec.py` (its own comment already says
   *"consumes EventSpec.delivery"*). To avoid two enums drifting (the RC-3 `Lane` lesson), the **canonical
   home is `sb/spec/events.py`** (the manifest leaf, alongside `EventSpec`); K7's `EventEmitSpec.delivery`
   **imports** it. Same two members (`AT_LEAST_ONCE`, `BEST_EFFORT`) — a pure re-home, not a divergence.
2. **`enqueue_audit_action` is a *twin*, not an edit of `emit_audit_action`.** The frozen vocab §③.2 pins
   `emit_audit_action`'s 11-field bus-emit signature (shipped `audit_events.py:52`) — I do **not** change it.
   The durable path is a **new** in-txn function carrying the identical payload (with `occurred_at`
   serialized `.isoformat()` per the §6.5 codec, exactly as `audit_events.py:87` already does on the bus);
   `emit_audit_action` stays the best-effort fallback. Both deliver the identical `EVT_AUDIT_ACTION_RECORDED`
   event, so `server_logging._on_audit_action` (the `bus.on` subscriber, verified `server_logging.py:773-787`,
   `**_extras`) is untouched.
3. **`pool.py:170-182 transaction()` docstring is now half-superseded — flag, don't edit yet.** Its
   *"EventBus emission belongs AFTER this context exits … never inside it"* is correct for **best-effort**
   emission but the outbox deliberately writes the **event-delivery row** inside the txn (the event *value*
   is captured in-txn; the *bus emit* still happens post-commit via the relay). When K3 lands, the docstring
   should be amended to: "best-effort bus.emit belongs after commit; `AT_LEAST_ONCE` events are captured
   in-txn via `outbox.enqueue(conn,…)` and delivered post-commit by the relay." Recorded here for the K3
   builder; not a divergence from the shipped transactional guarantee.
4. **The relay adopts the scheduler's `PollLane`/`PollSupervisor` port (reconciles 09 §3.6/§4/§8).** This
   doc's earlier draft modeled the relay as a standalone `RELAY_TASK` `ManagedTaskSpec` + a
   `relay_poll(...)->RelayCycleReport` on its own `Interval(seconds=1)` loop, wired by the composition root.
   **The scheduler ⑦ owns the poll infrastructure** and explicitly chose "one `PollSupervisor`, registered
   lanes" over "scheduler+outbox+janitor = 3 loops" (09 §8 "Poll topology"), and lists `OutboxRelayLane` as a
   consumed `PollLane` (09 §4). **Corrected:** the relay is `OutboxRelayLane` implementing
   `PollLane.tick(now)->LaneTickResult` + a no-op `reconcile_on_boot`, registered via
   `PollSupervisor.register_lane` (§3.4). The parallel `RELAY_TASK`/`RelayCycleReport`/`Interval(1s)`/
   composition-root-loop model is **deleted**. Consequences reconciled: **poll cadence** = the supervisor's
   5s (not 1s; §9 deferral 2); **return type** = `LaneTickResult` (not `RelayCycleReport`); **readiness/drain
   gate** = supervisor-central (not a lane-local `is_running()` step-0; §3.4 step 0 explains why the
   RUNNING-only vs `can_accept_commands()` distinction collapses for this lane); **error handling** = per-DEAD-row
   `record_operator_finding` inside `tick` + supervisor-caught+logged lane exceptions (the `PollLane` model
   has **no** per-lane `error_policy` — the earlier `error_policy="escalate_finding"` string is dropped, and
   09 §3.1's `ErrorPolicy` enum is a `ManagedTaskSpec` field, not a `PollLane` one).
5. **`enqueue_all` is a two-call protocol; `07:192,236` must change.** The outbox owns the `enqueue_all`
   body **and its return protocol** (07 says so: "I own the body"). It is **one in-txn call at K7 step 4**
   that writes the `AT_LEAST_ONCE` rows and *returns* a `BestEffortBatch`; the caller invokes
   `batch.emit_after_commit()` **after commit (step 6)**. `07-workflow-engine.md:192` makes a single call
   and its §4 Consumes row (`:236`) drops the return — under 07's own text the best-effort events **never
   emit**, and its "step-6 call" phrasing mis-locates the in-txn write to a committed conn. **07 must adopt
   the two-call protocol** (in-txn `enqueue_all` at step 4; `emit_after_commit()` at step 6). This doc's §3.3
   / §4 Provides state the corrected shape; 07's §3.3 step 6 + §4 Consumes are the loser text.
6. **Moving the direct-lane emits in-txn requires a conn-accepting producer form (verified prerequisite).**
   The retirement asserts `settings_mutation`'s and `xp_service`'s post-commit emits "move inside the txn."
   Verified: `settings_audit.set_value_with_audit` (called `settings_mutation.py:338`) and `db.add_xp`
   (called `xp_service.py:124`) each **own their transaction internally and accept no external `conn`** — so
   the emits *cannot* simply move in-txn without a refactor. **Prerequisite (owned by each direct-lane
   adopter, gated by the §13 OD-1 opt-in):** the producing mutation opens **one** `db.transaction()` and
   threads `conn` to **both** the effect and `enqueue(conn,…)`. Concretely: `set_value_with_audit` gains a
   `conn`-accepting form (or the pipeline opens the txn and calls the underlying conn-aware CRUD +
   `settings_audit` directly), and `add_xp` gains a `conn`-accepting form. This is a mechanical refactor over
   K3's conn-aware CRUD, **not** a fork — but it is a real cross-seam prerequisite a builder must schedule
   *before* an event can be flipped to `AT_LEAST_ONCE`. Best-effort events need no such change.

---

## 13. Open decisions (owner-gated — NOT decided here)

The **mechanism** is fully built and default-safe (every event is `BEST_EFFORT` until opted in — zero
behavior change). One decision is genuinely owner-gated and is surfaced here as the single landing site
(§3.1, §8 fork A, §9 deferral, §10 T2-3 point here):

| # | Decision | Options | Recommendation (built default) | Tier / gate |
|---|---|---|---|---|
| **OD-1** | **Which concrete events are `delivery=AT_LEAST_ONCE`** (the durable-delivery membership). Opting an event in also triggers the §12.6 conn-threading prerequisite for its producer. | (a) audit + reward only · (b) audit + all economy/coin events · (c) a broader guaranteed-delivery set the owner names | **(a) the v1 set: `audit.action_recorded`, `xp.awarded`, `xp.level_up`, `economy.balance_changed`.** Bounded by the KNOWN_EVENTS corpus; every other event stays `BEST_EFFORT`. | Tier-2, **owner-gated** (a data-durability/retention policy — each opt-in adds durable rows + a producer refactor). Recorded here; when the owner rules, this table is the durable home (mirror to a router Q if the owner wants it tracked there). |

---

*Written 2026-07-04 over the frozen `shared-vocabulary.md` (§③/§④/§⑤) + the two written strand-2 siblings
(K7 workflow-engine `07`, scheduler `09`), spot-verified against shipped source this session
(`utils/db/pool.py:170-182`, `services/audit_events.py:52-99`, `services/settings_mutation.py:330-409`,
`services/xp_service.py:120-150`, `core/events.py:100-152`, `services/server_logging.py:773-787,1856`;
design-spec §2.8/§5.3/§6). **NOT SOURCE OF TRUTH for runtime** — a design contract for K4/K7 and the durable
audit+reward paths to build ON. Relay integration adopts the scheduler's `PollLane` port (§12.4); the
`enqueue_all` two-call protocol and the direct-lane conn-threading prerequisite flag changes 07 and the K3
producers must absorb (§12.5, §12.6).*
