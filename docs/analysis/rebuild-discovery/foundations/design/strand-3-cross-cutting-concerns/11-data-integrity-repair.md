# Strand-3 · Cross-Cutting Concern (b) — Production-Data Integrity / Repair — Buildable Design Spec

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B design contract. Precedence: shipped source &
> merged PRs > the five strand-1 specs (for shapes they own) > the frozen `shared-vocabulary.md` >
> the two written strand-2 siblings (`07`, `09`) > this doc. This dossier **closes one
> never-surfaced foundational concern to design depth**: *every oracle in the rebuild proves CODE
> pre-ship; nothing sweeps or repairs live DATA, and CUT-2 would inherit corrupt rows as ground
> truth* (FJ `final-judgment-fable5-2026-07-03.md` §4 #7; L-1; L-18).
>
> **Consumes the FROZEN shared vocabulary — never redefines it:** the audit-row semantics (③
> `emit_audit_action`, 11 fields, `audit_events.py:52` verified), the idempotency-key contract
> (④ `IdempotencyKey`/`once`/`record_outcome`/`read_outcome` + `db.transaction()`), the error envelope
> (① `from_exception` + the frozen background `Surface.MAINTENANCE` member, 02 §3.1), `resolve_authority`
> scripted-bypass (②.3, `actor_type ∈ {system, backfill}`),
> the config/settings rail (⑥, the 4th kernel rail), and the frozen ref-kinds (⑩ `refs.py`:
> `ProviderRef` for a registered pure-read reader, `WorkflowRef` for an audited K7 mutation). It
> **builds on** two written strand-2 siblings: the K7 workflow engine (`07-workflow-engine.md`) and the
> durable scheduler (`09-scheduler-state.md`). Design against frozen decisions Q-0219…Q-0237 — never
> re-decided here.
>
> **Source-wins grounding (Q-0120), re-verified this session.** There is **no shipped `WorkflowResult`
> class** and **no `disbot/core/contracts.py`** — both are design-spec-only names (vocab §0). The **real**
> result-grammar seams are `disbot/services/lifecycle/contracts.py` (`LifecycleResult:77`,
> `LifecyclePreview:66`, `StepResult:56`, the five outcome constants `:48-52`, the three reversibility
> constants `:40-42`); the shipped **dispatch-result analogue** is `StageResult`
> (`disbot/core/runtime/message_pipeline.py:181`), which never crosses `resolve()`. K7's `WorkflowResult`
> is the **design superset** of `LifecycleResult` (design §2.7) — spec-only, never a shipped class. This
> dossier reads only `WorkflowResult.{outcome, mutation_id}` (both design §2.7 fields), never a shipped
> class.
>
> **The two K7/scheduler seams I stand on (verified against the written siblings this session):**
> - **K7 `run_ref(ref, ctx, *, conn=None) -> WorkflowResult`** is **OWNED and written** by `07` §3.2
>   (lines 221-232), the **external-conn entry** (`conn` provided ⇒ runs the resolved `CompoundOpSpec`'s
>   **DB legs + one central audit row + `AT_LEAST_ONCE` enqueue on the CALLER's `conn`**, opens **no** txn,
>   calls **no** `once()`/`record_outcome` — the caller owns dedup — runs **no** EFFECT/`BEST_EFFORT` legs
>   — the caller owns commit). `09` §4 consumes it verbatim as "the scheduler `_fire` target." My repair
>   rides this **identical** external-conn seam (§2.2). *(The earlier "assumed sibling shape" framing is
>   superseded — `run_ref` is written, not assumed; seam-correction §8.3.)*
> - The **always-on `PollSupervisor` + `PollLane` port** (`09` §3.6) I register a lane on, and the frozen
>   `IdempotencyKey`/`once` substrate (④) I use as my dual-instance cadence guard (§2.2).
>
> **Spot-verified against shipped source this session** (load-bearing seams only, per method): the RPS
> corrupt-row pattern `cogs/rps_tournament/_persistence.py:104-115` (read in full); `emit_audit_action`
> `services/audit_events.py:52` (11 kw-only fields); the economy aggregate-vs-ledger split
> `utils/db/economy.py:88` (`insert_economy_audit`, the ledger append) vs `:200`/`:210` (bare aggregate
> writes `add_coins`/`set_coins`, no ledger row); and `services/economy_service.py:253-254` — a ledger
> append that **is** audited on the money axis **but is itself the raw-`conn.execute` `utils/db`-boundary
> violation** `07` retires by re-homing it as a DB leg (seam-correction §8.5 — *not* held up as the clean
> seam). Source wins (Q-0120).

---

## 0. The one-line boundary vs. spec 09 (anti-pad — read this first)

Spec 09 already closes **version-drift** recovery: a row whose *schema version* drifted across a deploy
(`row.version != StoreSpec.payload_version`) is refunded / upcast / dropped at **load time** by
`resolve_versioned_load`. **But its step-0 is the exact hole I close:** `row.version ==
payload_version ⇒ resume, no policy — the common path. Return.` (09 §3.3). A row whose **schema is
current** but whose **content violates a declared invariant** — double-XP residue from a #1693-class
double-fire that wrote *both* aggregate and ledger at the current version, an orphaned escrow, a
double-settled session, an unaudited `set_coins` mint — **is never re-examined by anything, ever.**
Version-drift fires only on a `VERSION` bump and only touches the loaded row; my concern is
steady-state semantic corruption in current-version rows, plus the CUT-2 copy that inherits it.
**Everything below is the load-time-blind, content-level complement to 09 — not a re-derivation of it.**

---

## 1. THREAT / FAILURE MODEL

Every oracle the rebuild defines verifies **code, pre-ship**: goldens (byte-parity), compile fences
(`version_policy_declared`, `audit_completeness`, `leaderboard-has-writer`), K7 `preview()` dry-runs,
the importer's coverage reconciliation. **None reads a live row against a rule.** The corruption
already in prod — and any that a future bug injects — is invisible to all of them and becomes CUT-2's
ground truth.

| # | Scenario (who / what / how) | Grounded in | Blast radius |
|---|---|---|---|
| **T-1** | **Double-XP / double-credit residue.** A deploy-overlap double-fire (L-6) or a farm-collect double-credit (07 §1, `farm_workflow.py:114-179` no `once()`) writes *both* the aggregate and the ledger twice at the **current** version. 09's load-time policy never fires (versions match); no sweep exists. The residue is permanent, self-consistent, and indistinguishable from a legitimate balance. | L-6, L-1, 07 §1 | Real player currency inflated silently across every guild touched during an overlap window; compounds every deploy; becomes the CUT-2 baseline. |
| **T-2** | **Aggregate ⊄ ledger drift.** The spendable balance is the stored aggregate `xp.coins`; the audit trail is the separate `economy_audit_log`. A path that bumps the aggregate without appending the ledger — `set_coins`/`add_coins` (`economy.py:200`/`:210`, bare writes; the ledger append `insert_economy_audit` lives at `:88` and is only *sometimes* wrapped) — diverges the two. INV-F is a **sole-writer AST fence** (compile-time); it does **not** assert `xp.coins == baseline + Σ economy_audit_log.delta` at rest. | `economy.py:88` vs `:200`/`:210`; INV-F is code-fence-only (design §5.3 hazard 6) | The operator's audit answer ("where did these coins come from?") is unanswerable; a mint with no ledger row is un-forensicable; the divergence never self-heals. |
| **T-3** | **Orphaned value-bearing escrow.** A paid entry-fee row (`game_state`, `state={"bet": n}`, `_persistence.py:65-72`) is stranded when the bot crashes between debit and settle. Recovery *clears* it (RPS: `:104-115` clears w/o refund on version mismatch; 09 fixes the version-mismatch leg — but a **current-version** orphan whose owning session simply vanished is not a version mismatch and 09's load-path only runs on the drop-vs-resume decision, not "is this escrow still live?"). | `_persistence.py:104-115`, `:251-270` (the known-good refund proves the pattern) | Real money locked in a dead row; the 24h GC backstop only fires on the `bet` convention and only if no earlier path cleared it — a per-cog lottery, not an invariant. |
| **T-4** | **Terminal-once violated (double-settle).** `SettleOnceMixin` (`utils/terminal_guard.py:44`, design §2.8) is a *runtime* guard on the state seam; a crash-retry or a race that produces **two terminal rows for one session** leaves both persisted. Nothing re-checks "≤1 settle per session" after the fact. | design §2.8 `settle_once`, L-5 (panel re-entry), L-6 | A tournament pot paid twice; a wager settled to both parties; audit shows two winners for one game. |
| **T-5** | **The CUT-2 verify gap — corruption laundered into the new ledger-of-record.** The importer's dry-run reconciliation (§5.2) proves **coverage**: row counts, per-table checksums *old==new*, key coverage, stop-codes. A checksum that matches old==new **actively guarantees** T-1…T-4 corruption is carried faithfully. CUT-3 runs freeze→import→swap with **no correctness check between** (§5.4; L-18 "no gate requires verified restores"). | §5.2, §5.4, L-18, FJ §4 #7 | The new bot's very first state is silently corrupt; the corruption is now "original" (no old-bot to diff against post-cutover); rollback (L-18) can't undo writes made on the corrupt base. |
| **T-6** | **Abuse / self-inflicted mass-corruption.** A bad deploy, a broken migration, or a hostile input flips *many* rows at once. With no sweep there is no detector; **with a naïve sweep there is a new footgun** — an auto-repair that mutates thousands of rows on one buggy check erases the evidence and could itself be the bug. Any repair mechanic must be bounded and evidence-preserving by construction. | Design constraint (rubric class 13, FJ §8; the #1693 "cleared even on refund failure" anti-pattern, §5 gap 1) | Either blind to a mass event, or (naïvely built) an amplifier of one. |

**The through-line:** T-1…T-4 are *continuous steady-state* failure modes (they need a permanent
detector, not a cutover script); T-5 is the *one-time* cutover inheritance; T-6 is the *safety
envelope* any repair must satisfy. The design below answers all three shapes with one mechanic applied
at two points.

---

## 2. DESIGN RESPONSE

One mechanic — **declared invariants → scheduled dry-run sweep → audited repair / quarantine** —
plus a **CUT-2/CUT-3 verify step** that is the *same sweep* run against imported / restored data.
Buildable depth on the grammar + lane + repair seam; the two genuinely owner-only calls (auto-repair
posture, and the per-invariant *money-direction* of a value-bearing repair) are pushed to §4, decided
nowhere here.

### 2.1 `InvariantSpec` — the declared-invariant grammar (new leaf; a §2.8 sibling of `StoreSpec`)

A manifest-level facet (`data_invariants`, sibling to `stores`), **not** a `StoreSpec` field — a
reconciliation invariant spans *two* stores (aggregate vs ledger), so it cannot live on one. No logic
in the manifest (§2.9): the check and the repair are **registered refs** (frozen ref-kinds ⑩ — no new
ref-kind is introduced; `check_ref` is a `ProviderRef`, `repair_ref` a `WorkflowRef`).

```python
# sb/spec/invariants.py
#   leaf imports:  sb/spec/refs.py      (ProviderRef, WorkflowRef — frozen ⑩)
#                  sb/spec/scheduler.py (TaskScope — reused from 09's leaf; sb/spec→sb/spec is legal)
#   leaf defines:  InvariantKind, Severity, SweepCadence, InvariantSpec, Violation

class InvariantKind(StrEnum):
    ROW_PREDICATE  = "row_predicate"   # each row must satisfy P(row)                 (e.g. bet > 0)
    RECONCILIATION = "reconciliation"  # aggregate B == baseline + Σ ledger.delta     (xp.coins reconciles to economy_audit_log)
    UNIQUENESS     = "uniqueness"      # ≤1 row per natural key                       (double-fire ledger dupes)
    REFERENTIAL    = "referential"     # every row in A has a live referent in B       (escrow ⇒ live session)
    TERMINAL_ONCE  = "terminal_once"   # ≤1 terminal/settle row per session            (SettleOnceMixin at rest)

class Severity(StrEnum):
    REPAIRABLE     = "repairable"      # a safe audited repair exists (repair_ref REQUIRED)
    QUARANTINE_ONLY= "quarantine_only" # isolate + operator finding; never auto-mutate
    ALERT_ONLY     = "alert_only"      # metric + operator finding; no state change

class SweepCadence(StrEnum):           # maps to an interval, NOT a ManagedTaskSpec.trigger (the sweep is a PollLane, §2.2)
    ON_BOOT   = "on_boot"    # runs once per boot only (reconcile_on_boot); no steady-state tick
    HOURLY    = "hourly"     # 3600 s
    SIX_HOURLY= "six_hourly" # 21600 s
    DAILY     = "daily"      # 86400 s  (default)
    WEEKLY    = "weekly"     # 604800 s
# _CADENCE_SECONDS: Mapping[SweepCadence, int|None]  (ON_BOOT -> None) — the lane's due-ness math (§2.2)

@dataclass(frozen=True)
class InvariantSpec:
    invariant_id: str                  # [S] namespace kind `data_invariant` (K1-reserved; DISTINCT from
                                       #     StoreSpec.invariant_tag, which is the INV-F/G/K AST *sole-writer*
                                       #     fence — this is a *data-content* invariant, a different axis)
    kind: InvariantKind                # [S]
    owner_subsystem: str               # [S] the subsystem that owns the fix
    stores: tuple[str, ...]            # [S] table(s) the check reads; each must be a declared StoreSpec.table
    check_ref: ProviderRef             # [S] a REGISTERED pure-read reader; handler(spec, *, guild_id, conn) -> tuple[Violation,...]
                                       #     (frozen ⑩ ref-kind; body lives in the store's DOMAIN, resolved via K2 — §2.2 db-boundary note)
    severity: Severity                 # [S]
    repair_ref: WorkflowRef | None = None      # [S] REQUIRED iff severity==REPAIRABLE; an AUDITED K7 CompoundOpSpec that MUST
                                       #     satisfy 07's atomic_db_only fence (pure-DB legs, AT_LEAST_ONCE emits only, no EFFECT,
                                       #     no confirmation) — so it can run in run_ref external-conn mode on the sweep's txn (§2.2, fence §2.3)
    bears_value: bool = False          # [S] mirrors StoreSpec.bears_value — money/audit-bearing (drives the fence + the posture default)
    # ---- RECONCILIATION grammar (the satisfiable-against-real-data fix, T-2) ----
    baseline_ref: ProviderRef | None = None    # [S] REQUIRED iff kind==RECONCILIATION; handler(spec, *, guild_id, conn) -> Mapping[row_id,int]
                                       #     the per-key GENESIS OFFSET (reconciliation-epoch snapshot). See "the baseline" below.
    tolerance: int = 0                 # [S] allowed |drift| band (rounding / known benign noise); 0 = exact after baseline
    # ---- repair DIRECTION (the owner money call, §4 Q3) ----
    ground_truth_store: str | None = None      # [S] REQUIRED (fence §2.3) iff severity==REPAIRABLE AND bears_value AND
                                       #     kind in {RECONCILIATION, TERMINAL_ONCE}; names WHICH of `stores` is authoritative
                                       #     (the repair direction: reconcile the OTHER store to this one). Absent it, such an
                                       #     invariant may only be QUARANTINE_ONLY — the money direction is never guessed.
    # ---- posture (default; the LIVE enforce state is a runtime setting, §2.4 — NOT this constant) ----
    default_enforce: bool = False      # [S] the MANIFEST default posture (report-only). The operative per-invariant enforce
                                       #     state is settings-backed and flipped at runtime (§2.4); this is only its default.
    # ---- sweep bounds (T-6 circuit-breaker + read-volume bound) ----
    cadence: SweepCadence = SweepCadence.DAILY # [S] how often the sweep lane runs this check
    max_actions_per_run: int = 100     # [S] circuit-breaker cap on ACTIONS-OR-FINDINGS per run (BOTH postures — §2.2);
                                       #     overflow ⇒ STOP, quarantine the overflow, escalate a mass_corruption finding
    read_batch_size: int = 500         # [S] max rows check_ref reads per guild per tick — bounds the per-tick read volume
    scope: TaskScope = TaskScope.GUILD # [S] per-guild batched (reuses 09's TaskScope) — GLOBAL is a later band (§6)

@dataclass(frozen=True)
class Violation:                       # what a check_ref returns per bad row
    stores: tuple[str, ...]            # the store(s) this violation spans (subset of the invariant's stores in play)
    primary_store: str                 # the store whose row_id NAMES this violation — the quarantine / repair target
    row_id: str                        # the primary_store PK, rendered canonically. COMPOSITE keys (xp/economy keyed by
                                       #   (user_id, guild_id)) are ":"-joined in the StoreSpec's declared key-column order,
                                       #   e.g. f"{user_id}:{guild_id}" — the SAME rendering feeds dedup_token + quarantine identity.
    guild_id: int | None              # None for a GLOBAL-scope invariant
    fingerprint: str                   # stable hash of (invariant_id, primary_store, row_id, violating-value) — the dedup token
    detail: str                        # human reason ("aggregate=500, baseline=0, ledger=480, drift=+20 > tol=0")
```

**The check is a pure read; only `repair_ref` writes** — and it writes through K7's audited seam
(`WorkflowRef` → central audit row → `emit_audit_action`), never raw SQL. A `RECONCILIATION` check
reading two stores is fine: reads are unrestricted (`reader_domains`, §2.8, already models cross-store
reads). **`check_ref` is a `ProviderRef` (frozen ⑩), not a new ref-kind** — its body lives in the store's
domain and is resolved through the K2 ref table, **exactly** as 09's `active_rows_ref` reader does
(`09` §3.3), so the kernel sweep never imports a domain table (`xp`, `economy_audit_log`); it calls the
domain-registered reader through the ref seam (db-boundary note, §2.2 / §7).

**The baseline (why RECONCILIATION is satisfiable against real data — closes the flood).** `xp.coins ==
Σ economy_audit_log.delta` is **false for essentially every historical account**, because bare
`add_coins`/`set_coins` (`economy.py:200`/`:210`) never appended a ledger row and the ledger was added
mid-life. Exact equality would flag the entire economy → flood quarantine on the first run. So
`RECONCILIATION` is **not** `aggregate == Σ ledger`; it is `aggregate == baseline + Σ ledger.delta_since_epoch`
(within `tolerance`), where the **baseline** is a per-key genesis offset captured **once** at a
reconciliation epoch: `baseline[key] = aggregate[key] − Σ ledger.delta[key]` at the epoch instant. The
epoch is established at **CUT-2 import** (the natural clean line — §2.5 stage 3.5 snapshots it into the
new store) or, for a store already live, at the **first `enforce=True` flip** for that invariant. After
the epoch, the check flags **only post-epoch divergence** — a genuine new drift (a `set_coins` mint with
no ledger row *after* the baseline was drawn), never the pre-ledger history. `baseline_ref` is the
registered reader that returns `{row_id: genesis_offset}`; a store with no baseline snapshot yet (epoch
not drawn) resolves `baseline = 0` and the invariant stays report-only until the epoch is drawn (the
fence §2.3 requires `baseline_ref` present, not the snapshot populated — the snapshot is a data step).

### 2.2 The `InvariantSweepLane` — a `PollLane` on 09's always-on supervisor (peer to the due-queue + draft janitor)

**Architecture decision (closes the two-architectures ambiguity).** The sweep is a **distinct
`PollLane` registered on 09's existing `PollSupervisor`** (09 §3.6), a **peer** of the `DueQueueLane`
and the draft `ExpiryJanitorLane` — exactly the shape of the draft janitor (a lane with its own cadence
logic, `09` §3.6/§4). It is **NOT** a second `sb_due_queue` claim loop, and it is **NOT** a
`ManagedTaskSpec` fired by `DueQueueLane`. Both rejected, deliberately:

- *Not a `ManagedTaskSpec` fired by `DueQueueLane`:* `DueQueueLane` fires **one atomic `CompoundOpSpec`
  in one txn** (09 §3.7, `atomic_db_only`). A sweep is intrinsically a **bounded loop of independent
  idempotent repairs** — each its own txn, each its own `once()`, capped by a circuit-breaker across
  many guilds. That does not fit "one pure-DB op in one txn," so a sweep cannot be a due-queue fire.
- *Not a second `sb_due_queue` claim loop:* that would contend `DueQueueLane`'s table (the critic's race).

**Dual-instance cadence guard = the frozen ④ `once()` substrate (no new claim/lease store).** The lane
needs at-most-once-per-cadence-window across the fast-release overlap. It gets it **for free** from K3,
the same way 09's fire does (deterministic `dedup_token`, 09 §3.7) — **no** `sb_due_queue` read, **no**
new lease table:

```python
# sb/kernel/invariants/sweep.py

class InvariantSweepLane:              # a 09 PollLane (peer to DueQueueLane + ExpiryJanitorLane)
    name = "invariant_sweep"
    async def tick(self, now) -> LaneTickResult:  ...
    async def reconcile_on_boot(self, now) -> None: ...   # re-run any cadence epoch whose guard is incomplete (crashed); bounded

# tick(now): for each declared InvariantSpec whose cadence is due at `now`:
#   epoch  = now_epoch // _CADENCE_SECONDS[inv.cadence]                # ON_BOOT -> handled only in reconcile_on_boot
#   key    = IdempotencyKey(namespace=f"{inv.invariant_id}.sweep", guild_id=0, dedup_token=str(epoch))
#   async with db.transaction() as conn:
#       if not await once(key, conn=conn): continue                    # another instance/earlier tick already claimed this window
#   # (guard committed; this instance owns this epoch's sweep)
#   run = await self._run_sweep(inv, now)                              # bounded per-guild batches (read_batch_size), dispatch below
#   async with db.transaction() as conn:
#       await record_outcome(key, run.outcome, result_ref=run.run_id, conn=conn)   # marks the epoch complete
#       await self._db.write_sweep_log(run, conn=conn)                 # ONE sb_invariant_sweep_log row (kernel-internal bookkeeping)
```

- The `{invariant_id}.sweep:{epoch}` `once()` key gives **at-most-once per cadence window per invariant
  across all instances** — the same guarantee 09 gets from `{task_id}:{fire_epoch}`, on the **same**
  frozen substrate. **Zero `sb_due_queue` contention** (different namespace, its own guard rows).
- `reconcile_on_boot(now)` re-runs any recent cadence epoch whose guard row shows an **incomplete**
  outcome (a crash mid-sweep left `once()` claimed but `record_outcome` unwritten). Repairs are each
  individually `once()`-guarded, so a re-run never double-repairs.

**Per-`Violation` dispatch — the fixed algorithm (buildable, zero further decisions).** `enforce` here is
the **operative** per-invariant state — `effective_enforce = get_setting(INVARIANT_ENFORCE(inv.invariant_id),
default=inv.default_enforce)` (the runtime toggle, §2.4), **not** `inv.default_enforce`:

| Severity | `effective_enforce == False` (default) | `effective_enforce == True` |
|---|---|---|
| `REPAIRABLE` | count + log the repair it *would* make (dry-run) | run `repair_ref` **idempotently** (below), audited; on repair failure ⇒ quarantine + finding (never leave half-fixed) |
| `QUARANTINE_ONLY` | count + log | soft-quarantine the row (below) + operator finding |
| `ALERT_ONLY` | count + log | operator finding + metric; **no mutation** |
| *any*, when a run reaches `max_actions_per_run` | **STOP** after the cap; escalate a `mass_corruption` finding (a report-only sweep over a mass event is bounded too) | **STOP** after the cap, quarantine the overflow, escalate `mass_corruption` (a buggy check or bad deploy cannot trigger a mass auto-mutation) |

The circuit-breaker caps **actions-or-findings**, so it bounds the report-only path over T-6's own
mass-corruption event, not just the auto-repair path.

**The idempotent repair — the 09 `_fire_one` pattern verbatim (vocab ④ + K7 `run_ref` external-conn):**

```python
key = IdempotencyKey(namespace=f"{inv.invariant_id}.repair",
                     guild_id=v.guild_id or 0,                        # GLOBAL-scope (guild_id None) uses 0, exactly as 09 §3.7
                     dedup_token=f"{v.row_id}:{v.fingerprint}")       # DETERMINISTIC — the 5th ④.2 site (§8.1)
async with db.transaction() as conn:                                 # the SWEEP owns this one txn
    if not await once(key, conn=conn):
        return _reproduce(await read_outcome(key, conn=conn))         # already repaired — no double-fix
    ctx = WorkflowContext(actor=SWEEP_ACTOR, guild_id=v.guild_id or 0,  # guild_id is int (07 §3.2) → `or 0` (09's _fire pattern);
                          request_id=key.render(), params={"violation": v})   # SWEEP_ACTOR.actor_type="backfill" ⇒ scripted bypass §②.3
    result = await engine.run_ref(inv.repair_ref, ctx, conn=conn)     # 07 §3.2 EXTERNAL-CONN: pure-DB legs + central audit +
                                                                     #   AT_LEAST_ONCE enqueue on MY conn; NO txn, NO once(), NO EFFECT
    await record_outcome(key, result.outcome, result_ref=result.mutation_id, conn=conn)
```

- **The single-txn atomicity is buildable — it is 09 §3.7 exactly.** Because `run_ref(conn=conn)` runs in
  **external-conn mode** (07 §3.2): the **sweep** owns the `db.transaction()`, the `once()` guard, and
  `record_outcome`; `run_ref` runs the repair's **pure-DB legs + the one central audit row + any
  `AT_LEAST_ONCE` enqueue on the sweep's `conn`**, opening no txn of its own and running no EFFECT/best-effort
  legs. So **`once()` + repair-DB-legs + central-audit + `record_outcome` all commit in ONE txn** — the
  "exactly-once and forensic" claim holds, on the written seam. This is why `repair_ref` MUST satisfy
  `atomic_db_only` (fence §2.3): a repair with an EFFECT leg or a confirmation could not ride the sweep's
  txn. **Any Discord output from a repair is an `AT_LEAST_ONCE` outbox emit** (a row `run_ref` writes on
  the sweep's conn, delivered post-commit by ⑥'s relay), never a post-commit EFFECT leg — the identical
  posture 09 states for scheduled fires (09 §3.4).
- **`SWEEP_ACTOR` — the system-fire sentinel.** `SWEEP_ACTOR = ActorRef(user_id=None,
  actor_type="backfill", member_tier=None, is_guild_operator=False, is_bot_owner=False, is_dm=False)`,
  mirroring 09's `SYSTEM_ACTOR` but carrying `actor_type="backfill"` (the data-repair member of the
  frozen scripted-bypass set §②.3, distinguishing sweep-repairs from scheduler-fires in the audit trail).
  This **consumes the same additive `ActorRef.actor_type` field 09 already flagged** (09 §4/§12 #1 — "
  `ActorRef` must add `actor_type: str = 'user'`"); K7 maps `AuthorityRequest.actor_type =
  ctx.actor.actor_type` (09 §4), so `resolve_authority` step-1 scripted-bypasses. I do **not** re-flag it
  as a new correction (seam-correction §8.4).
- **Every repair is exactly-once and forensic:** `once()` makes a re-run a no-op; K7's central row records
  `mutation_type="invariant_repair:<invariant_id>"`, `prev_value`/`new_value`, `actor_type="backfill"`,
  `mutation_id` — never a silent DB edit. This is the deliberate improvement over the #1693 stopgap, which
  mutated without an idempotency key or an audit trail (§5 gap 1), and over 09's identical `compensation_ref`
  stance (a failed repair leaves the row **quarantined, not half-applied**).
- **A repair exception's error envelope uses the frozen `Surface.MAINTENANCE` (① / PIN-4).** A sweep-repair
  is a **headless background fire** — no interaction surface, no interaction `TargetRef`. When `run_ref`
  raises, the sweep classifies the exception through the frozen envelope
  `from_exception(exc, surface=Surface.MAINTENANCE, target=None)` (02 §3.1/§3.3), then quarantines the row
  (never left half-applied). `MAINTENANCE` is the **single** background `Surface` member (02 §3.1) that both
  09's scheduler-fires and 11's sweep-repairs classify under — **not** a local `scheduler`/`maintenance`
  string. 02 widened `from_exception`'s `target` to `TargetRef | None` for exactly this headless case;
  `surface`/`target` only enrich `user_message`, which a headless fire discards. This consumes 09's identical
  §3.8 posture verbatim (`from_exception(exc, surface=Surface.MAINTENANCE, target=None)`) — one shared token,
  no fork.

**Soft-quarantine — evidence-preserving, never destroy.** For a `QUARANTINE_ONLY` row (or a REPAIRABLE
row whose repair failed): snapshot the row's identity + full payload into **`sb_quarantine`**
(`{quarantine_id, primary_store, stores, row_id, guild_id, invariant_id, snapshot_json, quarantined_at,
disposition=NULL}`) and record an operator finding — this **preserves the evidence** (the load-bearing
property). Disposition (repair / carry-as-is / declared-loss) is **owner-signed**, reusing the SF-g
REQUIRED-`disposition` pattern + the §5.2 owner-reviewed-dry-run discipline. For a cross-store
`RECONCILIATION`/`REFERENTIAL` violation, the snapshot is keyed on **`primary_store` + `row_id`**
(the named target) while `stores` records the full span, so "which row is quarantined" is never
ambiguous. **Read-exclusion of a quarantined source row** (a `quarantined_at` column on the source table
+ a `quarantined_at IS NULL` filter injected into every domain read path) is a **cross-cutting change
larger than v1 and is a labeled deferral (§6), gated behind a per-`StoreSpec` `quarantine_read_exclusion`
opt-in** — for v1 the source row stays **visible-but-flagged** pending the owner disposition, which is the
conservative choice because (a) the default posture is report-only (nothing is quarantined until the
owner flips `enforce`), and (b) `QUARANTINE_ONLY` is precisely the class where auto-mutation is unsafe, so
leaving the row readable until an owner decides beats silently hiding it. The evidence snapshot in
`sb_quarantine` is the durable record either way.

**The sweep's own bookkeeping** (`sb_invariant_sweep_log`, the per-run counts) is **kernel-internal
observability, not an auditable domain mutation** — exactly as 09 treats its due-queue bookkeeping
(09 §7). Only the *repair* is an auditable mutation (the central K7 row).

### 2.3 The compile fence — `invariant_coverage` (honesty mechanism, mirrors `leaderboard-has-writer`)

```python
# sb/kernel/invariants/compile.py
```
- **Value-bearing coverage, keyed on `checkpoint_class` (closes the escrow gap T-3).** Every `StoreSpec`
  with `bears_value=True` **MUST** be the subject of ≥1 `InvariantSpec` whose `kind` is in the set allowed
  for that store's `checkpoint_class`, else `SEMANTIC_VIOLATION` ("value_bearing_store_uncovered") →
  CI-red:
  - `checkpoint_class ∈ {AGGREGATE, LEDGER}` (money aggregates/ledgers) ⇒ `RECONCILIATION` **or** `TERMINAL_ONCE`.
  - `checkpoint_class == SESSION` (escrow / session value, e.g. `game_state` `bet`) ⇒ `REFERENTIAL` **or** `TERMINAL_ONCE`.
  *A money store you can't reconcile-or-refer is a store you can't trust.* (The earlier fence accepted only
  `RECONCILIATION|TERMINAL_ONCE` and wrongly rejected T-3's escrow, whose natural invariant is `REFERENTIAL`.)
- `severity==REPAIRABLE` without `repair_ref` ⇒ `SEMANTIC_VIOLATION`.
- `repair_ref` that is not a `WorkflowRef` (a bare `HandlerRef` bypassing the audited seam) ⇒
  `SEMANTIC_VIOLATION` (reuses vocab §③.4 `audit_completeness` — a repair *is* a mutating ref).
- **`repair_ref` must be `atomic_db_only` (consumes 07 §3.6).** A repair reachable here MUST resolve to a
  `CompoundOpSpec` that is pure-DB + `AT_LEAST_ONCE`-emits-only — no EFFECT legs, no `BEST_EFFORT` emit, no
  `confirmation` — else `SEMANTIC_VIOLATION` ("repair_not_atomic_db_only"). This is what makes the
  `run_ref(conn=conn)` external-conn repair (§2.2) sound; it mirrors 09 §3.4's "scheduler-fire = pure-DB fence."
- `kind==RECONCILIATION` without `baseline_ref` ⇒ `SEMANTIC_VIOLATION` ("reconciliation_needs_baseline")
  — an un-baselined reconciliation would flood quarantine (T-2).
- **`severity==REPAIRABLE` AND `bears_value` AND `kind ∈ {RECONCILIATION, TERMINAL_ONCE}` without
  `ground_truth_store` ⇒ `SEMANTIC_VIOLATION` ("value_repair_needs_direction").** This **forces the
  owner money-direction call** (§4 Q3) to be declared before a value-bearing reconciliation may
  auto-repair; absent it the invariant may only ship `QUARANTINE_ONLY`. The near-irreversible "claw the
  aggregate down vs mint ledger rows up" decision (§4 Q3) is therefore never guessed by a builder.
- `check_ref` must be a pure-read `ProviderRef` (no mutating ref reachable) — a check that writes is rejected.

### 2.4 Report-only by default → auto-repair is a one-way door (settings-backed, per-invariant, runtime)

Every `InvariantSpec` ships `default_enforce=False` (report-only). **The operative enforce state is a
per-invariant RUNTIME setting, not a manifest `[S]` constant** — the sweep reads `effective_enforce =
db.get_setting(INVARIANT_ENFORCE(invariant_id), default=spec.default_enforce)` at tick time, where
`INVARIANT_ENFORCE(invariant_id)` is a `settings_keys` constant (the sanctioned config/settings seam,
vocab ⑥ — never `os.getenv`, never a raw string key). An operator flips one invariant to enforce **at
runtime, deliberately, per invariant**, after the check has been clean-verified against ground truth a
few times (CLAUDE.md's adopt-with-a-kill-switch rule; the same one-way-door as `pending → ported` in
`parity.yml`). Because it is a setting, the flip is a live operator action — **not** a code edit +
redeploy. A report-only sweep is fully contained and reversible (it mutates nothing), so it is safe to
build and ship now; its landing site is the settings rail (§3), **not** a bespoke control-plane. (A
richer operator UI over these toggles is a labeled deferral, §6.)

### 2.5 The CUT-2 verify-import step + CUT-3 verified-restore — the *same sweep*, at the cutover seam

Insert one stage into the §5.4 migration plan, **between (3) golden-replay and (4) cutover**:

> **(3.5) Invariant verify-import.** Run the full `data_invariants` sweep in **dry-run**
> (`effective_enforce=False` forced) against the *imported* data (new schema, pre-swap). The importer's
> §5.2 reconciliation proves **coverage** (checksums old==new); this proves **correctness** (the copied
> rows satisfy the declared invariants). *Coverage-fidelity ≠ invariant-correctness* — a checksum match
> old==new proves the copy faithfully carried whatever was there, corruption included. **Stage 3.5 is
> also where each `RECONCILIATION` invariant's baseline epoch is drawn** (§2.1): the snapshot
> `baseline[key] = aggregate[key] − Σ ledger.delta[key]` is captured on the imported store, so the new
> bot's reconciliation is satisfiable from row zero and only *post-import* drift is ever flagged.

- **Two new §5.2 machine-readable stop-codes:** `invariant_violation` (a declared invariant fails on
  imported data) and `unrepaired_quarantine` (rows the sweep flagged, none auto-repaired at import).
- **Two new §5.4 compat-scoreboard lines:** `invariant_violations_by_id`, `quarantined_rows` — so
  "the copy is correct" is a **read-off, not a feeling** (the §5.4 posture, extended from coverage to
  correctness).
- **Import-repair posture:** at import a violating row is imported **as-is but flagged** (never
  auto-repaired into the new DB) — the owner reviews the quarantine manifest and signs the disposition,
  preserving forensics and never letting the new bot silently rewrite historical data.
- **Verified-restore (L-18) is the same mechanic at a different point:** a restore is "verified" iff it
  boots **and** the dry-run invariant sweep passes against it. CUT-3's verified-restore gate and CUT-2's
  verify-import step are one sweep run at two seams.

Whether stage (3.5) / the restore check **hard-blocks** the swap or is **advisory** is owner-gated (§4 Q2).

---

## 3. LANDING SITE (so it cannot evaporate — V-3)

| Response | Lands as | Concrete home |
|---|---|---|
| `InvariantSpec` leaf + `data_invariants` manifest facet | **Gate-0 grammar field** (a §2.8 taxonomy primitive, sibling to `StoreSpec`) | design-spec §2.8; new leaf `sb/spec/invariants.py` (imports `refs.py`, `scheduler.py`); `SubsystemManifest.data_invariants` |
| `invariant_coverage` fence (checkpoint-class coverage, `repair_ref` audited + `atomic_db_only`, `baseline`/`ground_truth` mandates) | **`manifest-validate` CI gate** (§6 required check #2), beside `leaderboard-has-writer` | `sb/kernel/invariants/compile.py` |
| `InvariantSweepLane` (a `PollLane`, cadence via `once()` guard, no `sb_due_queue` contention) | **Registered `PollLane` on 09's `PollSupervisor` — a kernel rail** | `sb/kernel/invariants/sweep.py`; registered in the composition root under K5, **peer** to 09's `DueQueueLane` + draft `ExpiryJanitorLane` (09 §3.6) |
| Idempotent audited repair | **K7 `run_ref(conn=…)` external-conn (07 §3.2) + vocab ④ `once()`**; the 09 `_fire_one` pattern verbatim | `sb/kernel/invariants/sweep.py` → `07-workflow-engine.md` §3.2 `run_ref` |
| `sb_quarantine` + `sb_invariant_sweep_log` tables | **Fresh-chain StoreSpecs** (§5.1) — `sb_quarantine` owner-signed disposition; `sb_invariant_sweep_log` kernel-internal | migration `000N_invariants.sql` (schemas below) |
| Report-only default + per-invariant runtime `enforce` | **`default_enforce=False` manifest default + a settings-backed one-way-door runtime toggle** (`INVARIANT_ENFORCE(id)` `settings_keys` constant, mirrors `pending→ported`) | `InvariantSpec.default_enforce`; the settings/config rail (⑥) |
| CUT-2 verify-import stage (3.5) + baseline-epoch draw + 2 stop-codes + 2 scoreboard lines | **CUT-2 migration-plan stage + §5.2 stop-code set + §5.4 compat scoreboard** | design-spec §5.2/§5.4; Q-0222 cutover amendment (FJ §8) |
| Verified-restore = boot + sweep-clean | **CUT-3 gate** (L-18's verified-restore leg) | Stage-3 consolidation / CUT-3 gate list |
| The sweep as runtime enforcement of cost/abuse + reliability | **Rubric class 11 (cost/quota — the repair budget) + class 13 (security/abuse + non-functional)** | rubric §8 additions (already owner-flagged in FJ §8) |

**Fresh-chain schemas (§5.1):**

```
sb_quarantine (
  quarantine_id  uuid        PRIMARY KEY,
  invariant_id   text        NOT NULL,
  primary_store  text        NOT NULL,       -- Violation.primary_store — the named target
  stores         text[]      NOT NULL,       -- the full span (cross-store violations)
  row_id         text        NOT NULL,       -- canonical PK (composite ":"-joined, §2.1)
  guild_id       bigint      NULL,
  snapshot_json  jsonb       NOT NULL,       -- the preserved row payload (evidence)
  quarantined_at timestamptz NOT NULL,
  disposition    text        NULL            -- owner-signed: repair | carry_as_is | declared_loss (SF-g pattern)
)   -- indexes: (invariant_id, quarantined_at DESC), (guild_id) WHERE guild_id IS NOT NULL

sb_invariant_sweep_log (                     -- kernel-internal observability (NOT an auditable mutation, 09 §7)
  run_id            uuid        PRIMARY KEY,
  invariant_id      text        NOT NULL,
  cadence_epoch     bigint      NOT NULL,     -- the once()-guarded window (§2.2)
  started_at        timestamptz NOT NULL,
  finished_at       timestamptz NULL,         -- NULL ⇒ crashed mid-run (reconcile_on_boot re-runs)
  enforce_effective boolean     NOT NULL,     -- the runtime toggle value this run saw (§2.4)
  guilds_scanned    int         NOT NULL DEFAULT 0,
  rows_read         int         NOT NULL DEFAULT 0,
  violations_found  int         NOT NULL DEFAULT 0,
  repairs_applied   int         NOT NULL DEFAULT 0,
  quarantined       int         NOT NULL DEFAULT 0,
  alerts            int         NOT NULL DEFAULT 0,
  breaker_tripped   boolean     NOT NULL DEFAULT false   -- max_actions_per_run hit ⇒ mass_corruption finding
)   -- index: (invariant_id, started_at DESC)
```

---

## 4. OWNER-GATED

| # | Decision | Options | Recommendation | Gate |
|---|---|---|---|---|
| 🔒 **Q1** | **Permanent runtime oracle vs one-time migration script.** *(the concern's first owner question)* | **(A)** permanent always-on sweep lane · **(B)** one-time verify-import script at cutover only · **(C)** permanent lane, **report-only by default** (`default_enforce=False`), with the cutover verify-import hard-checking the same invariants | **(C).** Corruption is *continuous*, not a cutover event (T-1…T-4 recur every deploy in steady state), so (B) re-inherits the FJ §4 #7 blindness the day after swap. (A)'s auto-repair is real mutation risk. (C) builds the permanent lane (≈one `PollLane` on infra 09 already owns), ships every invariant report-only (contained, reversible — mutates nothing), and flips individual invariants to auto-repair only as each check proves out. **Decide-able against the default; flagged for ratification because the concern marks it owner-gated.** | owner posture |
| 🔒 **Q2** | **verify-import + verified-restore as HARD CUT gates vs advisory.** *(the concern's second owner question)* | **(A)** HARD on all invariants (safest; but one false-positive check blocks cutover — and CLAUDE.md warns checks can lie) · **(B)** advisory scoreboard line only (matches §5.4 "read-off"; but a missed line lets corrupt money rows become ground truth) · **(C)** **HARD on `bears_value` `RECONCILIATION`+`TERMINAL_ONCE`** invariants, **advisory** on the rest, with an **owner-signed quarantine-manifest override** (the §5.2 dry-run + SF-g signed-disposition pattern) | **(C).** A genuine owner-only call — the cutover data-loss-vs-blocking-risk tradeoff, near-irreversible either way (a bad cutover on corrupt money, or a blocked cutover on a false positive). Money/settle correctness hard-gates; everything else is advisory; the override keeps a real false-positive from stranding the program. **Options+recommendation only.** | owner call |
| 🔒 **Q3** | **Repair DIRECTION for a value-bearing violation — which store is ground truth (the near-irreversible money call).** *(surfaced by the fence; never decided here)* | For `aggregate=500, ledger=480` on a value-bearing `RECONCILIATION`/`TERMINAL_ONCE`: **(A)** aggregate is ground truth ⇒ mint 20 ledger rows to match 500 (launders an unaudited mint into "audited") · **(B)** ledger is ground truth ⇒ claw the spendable aggregate down to 480 (destroys real player balance) · **(C)** neither auto-repairs — **`QUARANTINE_ONLY`**, owner signs each disposition | **(C) as the built default** — the fence (§2.3) makes a value-bearing repairable reconciliation **require** an explicit `ground_truth_store`, so absent an owner-signed direction such an invariant ships `QUARANTINE_ONLY` and never auto-mutates money. **The per-invariant direction (A vs B) is a genuine owner-only, near-irreversible call** and is set only when the owner declares `ground_truth_store`. **Options only — the money direction is decided nowhere in this dossier.** | owner call (money) |
| ✅ **Q4 — RESOLVED** | **`Surface` member for a sweep-repair's error classification (`from_exception` ①).** *(was a vocab-freeze fork across 09/11; now frozen for both at once — PIN-4)* | The frozen interaction `Surface` (RC-11) is `{SLASH, PREFIX, COMPONENT, MODAL, NL_INTENT, NL_ORCHESTRATION}` — none fits a headless background fire, and the earlier draft weighed a per-sibling `scheduler` vs `maintenance` string (the fork the vocab exists to kill). | **DECIDED (PIN-4):** the `Surface` enum (spec 02 §3.1) gains **ONE** background member **`MAINTENANCE = "maintenance"`** covering scheduler fires (09) *and* invariant sweep-repairs (11); `from_exception`'s `target` widens to `TargetRef | None`; a headless fire calls `from_exception(exc, surface=Surface.MAINTENANCE, target=None)`, where `surface`/`target` only enrich `user_message` (a headless fire discards it). **Both 09 and 11 use `surface=Surface.MAINTENANCE`** — the single shared token, NOT the earlier `scheduler`/`maintenance` per-sibling string. Fork closed. | vocab freeze — CLOSED |
| ▹ **Q5** | **Repair `actor_type` — reuse `backfill` vs a distinct `invariant_repair` actor.** | **(A)** reuse `backfill` (already in the frozen scripted-bypass set §②.3 — zero authority-surface change; distinguishes sweep-repairs from 09's `system` fires) · **(B)** add a reserved `actor_type="invariant_repair"` for finer forensic filterability (extends the §②.3 scripted set by one) | **(A) for v1** (zero change to K6 authority), with **(B) as an optional-additive forensic improvement** — a distinct actor makes "which mutations were sweep-driven?" a one-filter query. **Decide-able by design; flagged.** (B) touches the K6 scripted-bypass set → owner-gated if taken. | design default |

---

## 5. RETIREMENT MAP

| Row (FJ §2 L / §4 gap / §6 owner-queue) | How this dossier retires it | Status |
|---|---|---|
| **FJ §4 #7 — production data never audited or repaired; CUT-2 inherits corrupt rows** | The whole dossier: declared invariants + always-on report-only sweep (§2.1–2.4) closes the "never audited/repaired" leg; the CUT-2 verify-import stage 3.5 + baseline draw + stop-codes + scoreboard (§2.5) closes the "inherits corrupt rows" leg. | **CLAIMED / CLOSED** |
| **L-1 — the corrupt-row pattern this must catch** | **Co-owned with 09.** 09 closes the **version-drift leg** (`row.version != payload_version ⇒ refund`). I close the **live-residue leg** (`row.version == payload_version` but content violates an invariant — the double-fire residue 09's step-0 resumes untouched, §0). Different mechanism, same L-row. | **CLAIMED (live-residue leg; version-drift leg = 09)** |
| **L-18 — backup/DR + verified-restore + rollback disposition** | **Verified-restore leg CLOSED:** "verified" := boots + dry-run sweep clean (§2.5). The **rollback-data-disposition** leg stays owner-queued (a T2 addition, §6). | **PARTIALLY CLOSED (verified-restore leg)** |
| **Owner-queue T2 (Q-0222 amendment, FJ §8) — "verify-import step between freeze and swap"** | Exactly the CUT-2 stage 3.5 + the baseline draw + the two stop-codes + the two scoreboard lines (§2.5). | **CLAIMED / CLOSED** |
| **§5 residual gap 1 (#1693) — mutated even when the fix failed** | The repair path leaves a failed repair **quarantined, not half-applied** (`enforce` dispatch table, §2.2) — audited + idempotent, the deliberate improvement over the stopgap. Reinforces 09's identical stance on `compensation_ref` failure. | **CLOSED (reinforced)** |
| **Rubric class 11 (cost/quota) + 13 (security/abuse) — FJ §8** | The sweep is their **runtime enforcement arm** (repair budget = class 11; mass-corruption circuit-breaker = class 13). Feeds them; does not own the rubric edit. | **FEEDS (not owned)** |
| **FJ §4 #11 — ungoverned prod-data copies / retention in the proving pipeline** | The verify-import/verified-restore gate is where a restored snapshot's *correctness* gets a checkpoint; the snapshot's *retention/erasure lifecycle* is a separate privacy cut (rubric 12). | **ADJACENT (correctness checkpoint only; retention deferred, §6)** |

---

## 6. DEFERRALS (labeled)

| Deferral | Reason | Bound |
|---|---|---|
| **Soft-quarantine read-exclusion wiring** (a `quarantined_at` column on each value store + a `quarantined_at IS NULL` filter injected into every domain read path) | Cross-cutting — touching every domain reader is larger than v1, and the report-only default + `QUARANTINE_ONLY` conservatism make a *visible-but-flagged* row the safe v1 choice (§2.2). | v1 preserves evidence in `sb_quarantine` (the durable record) + operator finding; read-exclusion is gated behind a per-`StoreSpec` `quarantine_read_exclusion` opt-in, wired via `reader_domains` when the owner enables it. |
| **Retention / erasure lifecycle of restored snapshots** (FJ §4 #11) | Scope — a **privacy/retention** concern (rubric class 12), not data-*integrity*. The sweep gates a restore's *correctness*, not the copy's *lifetime*. | Pointer to the retention cross-cut; the verify gate is the hook it plugs into. |
| **A richer operator control-plane / UI over the `enforce` toggles** | v1's toggle is the settings-backed `INVARIANT_ENFORCE(id)` flag (§2.4); a dashboard over the toggles + sweep-log is presentation, not integrity. | v1 ships the settings flag + the `sb_invariant_sweep_log` read-off; a UI is a later band. |
| **Compensation-saga for a repair that itself needs multi-step rollback** | Out of the v1 corpus — identical bound to 09 §9 (A#26 "record without a saga engine"). | v1 quarantines + operator finding; `repair_ref` `WorkflowRef` is the forward seam. |
| **GLOBAL-scope / whole-DB single-pass invariants** | v1 sweeps **per-guild in bounded batches** (`read_batch_size`, matching the shipped per-guild economy read shape) with the `max_actions_per_run` cap. | A cross-guild global-scan invariant is a later band with a throughput budget (mirrors 09's `max_catchup`/bounded-batch posture). |
| **Automatic invariant *discovery*** (inferring invariants from the schema) | Invariants are **declared, never inferred** — matches §2.9 "the manifest contains no logic" and the declared-not-inferred discipline. | v1 ships hand-declared `InvariantSpec`s for the `bears_value` stores (economy, escrow, karma, XP) the fence requires. |
| **Rollback-data disposition** (L-18 second leg) | The reverse-import / replay / declared-loss decision is owner-gated with rollback-window N. | Stays a T2 owner-queue addition (FJ §3/§6); this dossier closes only the verified-restore leg. |

All deferrals sit behind a designed seam; none blocks building the grammar, the report-only sweep lane,
or the verify-import stage now.

---

## 7. Architecture rules honored (cited)

- **All repairs through the domain `*_mutation.py` seam + `emit_audit_action`** — a repair is a K7
  `WorkflowRef` run via `run_ref(conn=…)` external-conn (07 §3.2 → the central audit row →
  `emit_audit_action`, `audit_events.py:52`); the fence §2.3 rejects a bare-`HandlerRef` repair **and** a
  non-`atomic_db_only` repair. The sweep **never** writes a domain row itself.
- **All DB access via `utils.db.*` / `sb/kernel/db/*` (asyncpg only)** — `check_ref` is a domain-registered
  `ProviderRef` reader resolved through K2 (like 09's `active_rows_ref`); the **kernel sweep never imports a
  domain table** (`xp`, `economy_audit_log`) — it calls the domain reader through the ref seam, which reads
  via `utils.db.*`. The `sb_quarantine`/`sb_invariant_sweep_log` CRUD lives behind the db boundary; no raw
  `pool.execute` from the kernel sweep (unlike the shipped `automation_scheduler._fetch_due_rules`
  violation 09 §12 retires). *(Contrast `economy_service.py:253` — a ledger-appending but raw-`conn.execute`
  boundary violation 07 retires; not a model to copy, §8.5.)*
- **`services` must NOT import `views`; cogs never import cogs** — `sb/kernel/invariants/*` is kernel
  tier: imports `sb/spec/*`, `sb/kernel/db/*`, `sb/kernel/workflow/*` (K7), `sb/kernel/scheduler/*` (09);
  imports no view, no cog. Recovery/repair logic moves **out of** cog code into the kernel (a layering win).
- **`settings_keys` constants, never raw env** — the per-invariant `enforce` toggle is a `settings_keys`
  constant `INVARIANT_ENFORCE(id)` read via `db.get_setting` (§2.4); the cadence + bounds are `InvariantSpec`
  manifest fields, never `os.getenv`.
- **INV-F/G/K preserved** — the `xp.coins` reconciliation is INV-F territory; its `repair_ref` flows
  through the audited economy `CompoundOpSpec` (07 escrow/economy family), keeping every coin movement
  inside one audited txn. `InvariantSpec.invariant_id` is a **distinct** namespace axis (`data_invariant`)
  from `StoreSpec.invariant_tag` (the sole-writer AST fence) — no overload.

---

## 8. Seam corrections (flagged; source-wins Q-0120)

1. **Vocab §④.2's "three sites" table is non-exhaustive — additive, not wrong.** It enumerates dispatch
   dedup, confirm re-entry, and leg/relay dedup as the `IdempotencyKey` application sites. Spec 09
   already added a **4th** (the `{table}.version_reject:{...}` guard); my sweep adds **two 5th-class
   sites** constructed identically — the **cadence guard** `{invariant_id}.sweep:{epoch}` (§2.2) and the
   **repair guard** `{invariant_id}.repair:{row_id}:{fingerprint}`. Flagged so a builder does **not** read
   the list as closed. The contract shape is unchanged; only the site inventory grows. **No divergence — a
   completeness note on ④.2.**
2. **`Surface` member for a sweep-repair — RESOLVED at the vocab freeze (PIN-4).** `from_exception` (①)
   takes `surface`; a repair/compensation exception has no natural *interaction* `Surface`, and the frozen
   interaction `Surface` (RC-11) is `{SLASH, PREFIX, COMPONENT, MODAL, NL_INTENT, NL_ORCHESTRATION}` — the
   earlier draft weighed a per-sibling `scheduler` vs `maintenance` string. **The fork is now closed at the
   vocab:** the `Surface` enum (spec 02 §3.1) gains **ONE** background member **`MAINTENANCE = "maintenance"`**
   that covers scheduler fires (09) *and* invariant sweep-repairs (11) — the single shared token both siblings
   adopt at once, not a per-sibling string. `from_exception`'s `target` widens to `TargetRef | None`; a
   headless sweep-repair fire calls `from_exception(exc, surface=Surface.MAINTENANCE, target=None)`, where
   `surface`/`target` only enrich `user_message` (a headless fire discards it). **Both 09 (§3.8) and 11 (§2.2)
   use `surface=Surface.MAINTENANCE`.** The earlier "open fork / reuse 09's `scheduler`" framing is
   superseded by the frozen `MAINTENANCE` member — no divergence, no second token.
3. **`run_ref` is OWNED by 07, not assumed (source-wins clarification).** 07 §3.2 (lines 221-232)
   **writes** `run_ref(ref, ctx, *, conn=None) -> WorkflowResult` as the external-conn entry, and 09 §4
   consumes it as "PROVIDED … the scheduler `_fire` target." My repair rides the **same** written seam.
   The single-txn `once()`+repair+`record_outcome` atomicity (§2.2) is therefore buildable exactly as 09's
   `_fire_one` (09 §3.7): the sweep owns the txn + guard + `record_outcome`; `run_ref(conn=…)` runs the
   repair's pure-DB legs + central audit on the sweep's conn. The constraint this imposes — `repair_ref`
   must be `atomic_db_only` (07 §3.6) — is enforced by the fence §2.3. *(No shipped `WorkflowResult` class
   is cited; only the design §2.7 `{outcome, mutation_id}` fields — vocab §0.)*
4. **`ActorRef.actor_type` — consumed from 09's already-flagged additive field, not re-flagged.** The
   repair sentinel `SWEEP_ACTOR` carries `actor_type="backfill"` (§②.3 scripted-bypass). The frozen
   `ActorRef` (vocab ⑩) carries `{user_id, is_guild_operator, is_bot_owner, is_dm, member_tier}` and no
   `actor_type`; **09 §4/§12 #1 already surfaced** "`ActorRef` must add `actor_type: str = 'user'`" (the
   same additive-field correction RC-12 made for `member_tier`). I **consume** that correction — I do not
   raise it as new. K7 maps `AuthorityRequest.actor_type = ctx.actor.actor_type` (09 §4), so `"backfill"`
   scripted-bypasses at `resolve_authority` step 1.
5. **`economy_service.py:253-254` is the boundary-VIOLATION exemplar, not the clean audited seam.** It
   appends `economy_audit_log` (so it **is** audited on the money axis) **but** does so via a raw
   `conn.execute` — the `utils/db`-boundary violation 07 explicitly retires by re-homing `transfer` as a
   DB leg (07 §2/§10). The clean audited-money seam is the domain `*_mutation.py`/K7 `CompoundOpSpec` that
   appends the ledger via `utils.db.economy.insert_economy_audit` (`:88`); `:253` is cited here only as the
   *anti-pattern* a repair must not reproduce. (This corrects the earlier header's use of `:254` as the
   "audited path" exemplar.)

*Written 2026-07-04 against the frozen shared vocabulary (`../shared-vocabulary.md`, all-five-pass) and
the two written strand-2 siblings (`../strand-2-runtime-durability/07-workflow-engine.md` — `run_ref`
§3.2 verified owned; `09-scheduler-state.md` — `PollSupervisor`/`_fire_one`/`SYSTEM_ACTOR` verified).
Spot-verified against shipped source this session: `cogs/rps_tournament/_persistence.py:65-115,251-270`,
`services/audit_events.py:52`, `utils/db/economy.py:88,200,210`, `services/economy_service.py:253-254`.
**NOT SOURCE OF TRUTH for runtime** — a Phase-B design contract for the strand-3 cross-cutting build to
execute against.*
