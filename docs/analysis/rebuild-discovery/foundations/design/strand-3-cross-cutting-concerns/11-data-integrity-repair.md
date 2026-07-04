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
> (④ `IdempotencyKey`/`once`/`record_outcome` + `db.transaction()`), the error envelope
> (① `from_exception`), `resolve_authority` scripted-bypass (②.3, `actor_type ∈ {system, backfill}`),
> and the config/data-plane rail (⑥, the 4th kernel rail). It **builds on** two written strand-2
> siblings: the K7 workflow engine (`07-workflow-engine.md` — `run()`/`run_ref()`, the audited
> `emit_central_audit` seam, `preview()` dry-run) and the durable scheduler (`09-scheduler-state.md`
> — the always-on `PollSupervisor` + `PollLane` port I register a lane on, and `resolve_versioned_load`
> whose boundary I complete). Design against frozen decisions Q-0219…Q-0237 — never re-decided here.
>
> **Spot-verified against shipped source this session** (load-bearing seams only, per method): the RPS
> corrupt-row pattern `cogs/rps_tournament/_persistence.py:104-115` (read in full); `emit_audit_action`
> `services/audit_events.py:52` (11 kw-only fields); the economy aggregate-vs-ledger split
> `utils/db/economy.py:98` (ledger append) vs `:200-215` (bare aggregate writes `add_coins`/`set_coins`,
> no ledger row) + `services/economy_service.py:254` (the audited path). Source wins (Q-0120).

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
| **T-2** | **Aggregate ⊄ ledger drift.** The spendable balance is the stored aggregate `xp.coins`; the audit trail is the separate `economy_audit_log`. A path that bumps the aggregate without appending the ledger — `set_coins`/`add_coins` (`economy.py:200-215`, bare writes; the audited wrap lives only in `economy_service`) — diverges the two. INV-F is a **sole-writer AST fence** (compile-time); it does **not** assert `xp.coins == Σ economy_audit_log.delta` at rest. | `economy.py:98` vs `:200-215`; INV-F is code-fence-only (design §5.3 hazard 6) | The operator's audit answer ("where did these coins come from?") is unanswerable; a mint with no ledger row is un-forensicable; the divergence never self-heals. |
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
Buildable depth on the grammar + lane + repair seam; decision-ready depth on the two postures (§4).

### 2.1 `InvariantSpec` — the declared-invariant grammar (new leaf; a §2.8 sibling of `StoreSpec`)

A manifest-level facet (`data_invariants`, sibling to `stores`), **not** a `StoreSpec` field — a
reconciliation invariant spans *two* stores (aggregate vs ledger), so it cannot live on one. No logic
in the manifest (§2.9): the check and the repair are **registered refs**.

```python
# sb/spec/invariants.py  (leaf — imports sb/spec/refs.py, sb/spec/roles.py only)

class InvariantKind(StrEnum):
    ROW_PREDICATE  = "row_predicate"   # each row must satisfy P(row)            (e.g. bet > 0)
    RECONCILIATION = "reconciliation"  # Σ over store A must equal aggregate B   (xp.coins == Σ ledger.delta)
    UNIQUENESS     = "uniqueness"      # ≤1 row per natural key                  (double-fire ledger dupes)
    REFERENTIAL    = "referential"     # every row in A has a live referent in B (escrow ⇒ live session)
    TERMINAL_ONCE  = "terminal_once"   # ≤1 terminal/settle row per session      (SettleOnceMixin at rest)

class Severity(StrEnum):
    REPAIRABLE     = "repairable"      # a safe audited repair exists (repair_ref REQUIRED)
    QUARANTINE_ONLY= "quarantine_only" # isolate + operator finding; never auto-mutate
    ALERT_ONLY     = "alert_only"      # metric + operator finding; no state change

@dataclass(frozen=True)
class InvariantSpec:
    invariant_id: str                  # [S] namespace kind `data_invariant` (K1-reserved; DISTINCT from
                                       #     StoreSpec.invariant_tag, which is the INV-F/G/K AST *sole-writer*
                                       #     fence — this is a *data-content* invariant, a different axis)
    kind: InvariantKind                # [S]
    owner_subsystem: str               # [S] the subsystem that owns the fix
    stores: tuple[str, ...]            # [S] table(s) the check reads; each must be a declared StoreSpec.table
    check_ref: ValidatorRef            # [S] pure read → tuple[Violation]; a registered escape-hatch handler
    severity: Severity                 # [S]
    repair_ref: WorkflowRef | None = None      # [S] REQUIRED iff severity==REPAIRABLE; the AUDITED fix (K7)
    bears_value: bool = False          # [S] mirrors StoreSpec.bears_value — money/audit-bearing (drives the fence)
    enforce: bool = False              # [S] False ⇒ report-only (default; the one-way door, §2.4);
                                       #     True ⇒ auto-repair/quarantine live
    cadence: SweepCadence = DAILY      # [S] how often the sweep lane runs this check
    max_actions_per_run: int = 100     # [S] the circuit-breaker cap (T-6); overflow ⇒ quarantine + escalate
    scope: TaskScope = TaskScope.GUILD # [S] per-guild batched (reuses 09's TaskScope) — GLOBAL is a later band (§6)

@dataclass(frozen=True)
class Violation:                       # what a check_ref returns per bad row
    store: str
    row_id: str
    guild_id: int | None
    fingerprint: str                   # stable hash of (invariant_id, row_id, violating-value) — the dedup token
    detail: str                        # human reason ("aggregate=500, ledger=480, drift=+20")
```

**The check is a pure read; only `repair_ref` writes** — and it writes through the store's own audited
mutation seam (K7 `WorkflowRef` → `emit_audit_action`), never raw SQL. A `RECONCILIATION` check reading
two stores is fine: reads are unrestricted; `reader_domains` (§2.8) already models cross-store reads.

### 2.2 The `InvariantSweepLane` — a `PollLane` on 09's always-on supervisor (I build a lane, not a loop)

The sweep **registers on the existing `PollSupervisor`** (09 §3.6) exactly as the outbox relay and
draft janitor do. No new poll loop, no new enablement flag (kernel restart-safety is not opt-in, 09 §8).
Each invariant is armed as a **DURABLE recurring `ManagedTaskSpec`** (09 §3.1) so its cadence survives
merge=deploy and boot-reconciles.

```python
# sb/kernel/invariants/sweep.py

class InvariantSweepLane:              # a 09 PollLane
    async def tick(self, now) -> LaneTickResult: ...
    #   claim the next-due invariant timer → run its check_ref over stores in BOUNDED per-guild batches
    #   → for each Violation, dispatch by severity (below) → write ONE sb_invariant_sweep_log row
    async def reconcile_on_boot(self, now) -> None: ...   # run any overdue sweep once (09 misfire=COALESCE)
```

**Per-`Violation` dispatch — the fixed algorithm (buildable, zero further decisions):**

| Severity | `enforce=False` (default) | `enforce=True` |
|---|---|---|
| `REPAIRABLE` | count + log the repair it *would* make (dry-run) | run `repair_ref` **idempotently** (below), audited; on repair failure ⇒ quarantine + finding (never leave half-fixed) |
| `QUARANTINE_ONLY` | count + log | soft-quarantine the row (below) + operator finding |
| `ALERT_ONLY` | count + log | operator finding + metric; **no mutation** |
| *any*, when a run exceeds `max_actions_per_run` | — | **STOP** after the cap, quarantine the overflow, escalate a `mass_corruption` finding (T-6 circuit-breaker — a buggy check or a bad deploy cannot trigger a mass auto-mutation) |

**The idempotent repair — reuses 09's `_fire` pattern verbatim (vocab ④ + K7):**

```python
key = IdempotencyKey(namespace=f"{inv.invariant_id}.repair",
                     guild_id=v.guild_id or 0,
                     dedup_token=f"{v.row_id}:{v.fingerprint}")     # DETERMINISTIC — the 5th ④.2 site (§ seam note)
async with db.transaction() as conn:
    if not await once(key, conn=conn):
        return _reproduce(await read_outcome(key, conn=conn))       # already repaired — no double-fix
    ctx = WorkflowContext(actor=sweep_actor, guild_id=v.guild_id,   # actor_type="backfill" ⇒ scripted bypass §②.3
                          request_id=key.render(), params={"violation": v})
    result = await engine.run_ref(inv.repair_ref, ctx, conn=conn)   # AUDITED inside K7 → emit_audit_action (§③)
    await record_outcome(key, result.outcome, result_ref=result.mutation_id, conn=conn)
```

- **Every repair is exactly-once and forensic:** `once()` makes a re-run a no-op; K7's central row records
  `mutation_type="invariant_repair:<invariant_id>"`, `prev_value`/`new_value`, `actor_type="backfill"`,
  `mutation_id` — so a repair is never a silent DB edit. This is the deliberate improvement over the
  #1693 stopgap, which mutated without an idempotency key or an audit trail (§5 gap 1).
- **Soft-quarantine, never destroy** (a `bears_value` row): move the row's identity into `sb_quarantine`
  (`{store, row_id, invariant_id, snapshot_json, quarantined_at, disposition=NULL}`) and mark the source
  row excluded-from-normal-reads (a `quarantined_at` column), preserving the evidence. Disposition
  (repair / carry-as-is / declared-loss) is **owner-signed**, reusing the SF-g REQUIRED-`disposition`
  pattern and the §5.2 owner-reviewed-dry-run discipline.
- **The sweep's own bookkeeping** (`sb_invariant_sweep_log`, the per-run counts) is **kernel-internal
  observability, not an auditable domain mutation** — exactly as 09 treats its due-queue bookkeeping
  (09 §7). Only the *repair* is an auditable mutation.

### 2.3 The compile fence — `invariant_coverage` (honesty mechanism, mirrors `leaderboard-has-writer`)

```python
# sb/kernel/invariants/compile.py
```
- Every `StoreSpec` with `bears_value=True` **MUST** be the subject of ≥1 `RECONCILIATION` **or**
  `TERMINAL_ONCE` `InvariantSpec` ⇒ else `SEMANTIC_VIOLATION` ("value_bearing_store_uncovered") → CI-red.
  *A money store you can't reconcile is a store you can't trust.*
- `severity==REPAIRABLE` without `repair_ref` ⇒ `SEMANTIC_VIOLATION`.
- `repair_ref` that is not a `WorkflowRef` (i.e. a bare `HandlerRef` bypassing the audited seam) ⇒
  `SEMANTIC_VIOLATION` (reuses vocab §③.4 `audit_completeness` — a repair *is* a mutating ref).
- `check_ref` must be pure-read (no mutating ref reachable) — a check that writes is rejected.

### 2.4 Report-only by default → auto-repair is a one-way door (the CLAUDE.md "unverified" discipline)

Every `InvariantSpec` ships `enforce=False` (report-only): the sweep runs, finds violations, and writes
them to the scoreboard — **but mutates nothing** until an operator flips `enforce=True` per invariant,
deliberately, after the check has been clean-verified against ground truth a few times (CLAUDE.md's
adopt-with-a-kill-switch rule; the same one-way-door as `pending → ported` in `parity.yml`). A
report-only sweep is fully contained and reversible — it is safe to build and ship now.

### 2.5 The CUT-2 verify-import step + CUT-3 verified-restore — the *same sweep*, at the cutover seam

Insert one stage into the §5.4 migration plan, **between (3) golden-replay and (4) cutover**:

> **(3.5) Invariant verify-import.** Run the full `data_invariants` sweep in **dry-run** against the
> *imported* data (new schema, pre-swap). The importer's §5.2 reconciliation proves **coverage**
> (checksums old==new); this proves **correctness** (the copied rows satisfy the declared invariants).
> *Coverage-fidelity ≠ invariant-correctness* — a checksum match old==new proves the copy faithfully
> carried whatever was there, corruption included.

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
| `InvariantSpec` leaf + `data_invariants` manifest facet | **Gate-0 grammar field** (a §2.8 taxonomy primitive, sibling to `StoreSpec`) | design-spec §2.8; new leaf `sb/spec/invariants.py`; `SubsystemManifest.data_invariants` |
| `invariant_coverage` fence (bears_value ⇒ covered) + `severity/repair_ref` fences | **`manifest-validate` CI gate** (§6 required check #2), beside `leaderboard-has-writer` | `sb/kernel/invariants/compile.py` |
| `InvariantSweepLane` (always-on, DURABLE recurring tasks) | **Registered `PollLane` on 09's `PollSupervisor` — a kernel rail** | `sb/kernel/invariants/sweep.py`; registered in the composition root under K5, exactly as 09's due-queue lane |
| Idempotent audited repair | **K7 `run_ref` (audited) + vocab ④ `once()`**; reuses 09's `_fire` pattern | `sb/kernel/invariants/sweep.py` → `07-workflow-engine.md` `run_ref` |
| `sb_quarantine` + `sb_invariant_sweep_log` tables | **Fresh-chain StoreSpecs** (§5.1) — the former `bears_value`-adjacent, owner-signed disposition | migration `000N_invariants.sql` |
| Report-only default + per-invariant `enforce` flip | **`enforce=False` grammar default + a one-way-door operator action** (mirrors `pending→ported`) | `InvariantSpec.enforce`; operator control-plane §6 |
| CUT-2 verify-import stage (3.5) + 2 stop-codes + 2 scoreboard lines | **CUT-2 migration-plan stage + §5.2 stop-code set + §5.4 compat scoreboard** | design-spec §5.2/§5.4; Q-0222 cutover amendment (FJ §8) |
| Verified-restore = boot + sweep-clean | **CUT-3 gate** (L-18's verified-restore leg) | Stage-3 consolidation / CUT-3 gate list |
| The sweep as runtime enforcement of cost/abuse + reliability | **Rubric class 11 (cost/quota — the repair budget) + class 13 (security/abuse + non-functional)** | rubric §8 additions (already owner-flagged in FJ §8) |

---

## 4. OWNER-GATED

| # | Decision | Options | Recommendation | Gate |
|---|---|---|---|---|
| 🔒 **Q1** | **Permanent runtime oracle vs one-time migration script.** *(the concern's first owner question)* | **(A)** permanent always-on sweep lane · **(B)** one-time verify-import script at cutover only · **(C)** permanent lane, **report-only by default** (`enforce=False`), with the cutover verify-import hard-checking the same invariants | **(C).** Corruption is *continuous*, not a cutover event (T-1…T-4 recur every deploy in steady state), so (B) re-inherits the FJ §4 #7 blindness the day after swap. (A)'s auto-repair is real mutation risk. (C) builds the permanent lane (≈one `PollLane` on infra 09 already owns), ships every invariant report-only (contained, reversible — mutates nothing), and flips individual invariants to auto-repair only as each check proves out. **Decide-able against the default; flagged for ratification because the concern marks it owner-gated.** | owner posture |
| 🔒 **Q2** | **verify-import + verified-restore as HARD CUT gates vs advisory.** *(the concern's second owner question)* | **(A)** HARD on all invariants (safest; but one false-positive check blocks cutover — and CLAUDE.md warns checks can lie) · **(B)** advisory scoreboard line only (matches §5.4 "read-off"; but a missed line lets corrupt money rows become ground truth) · **(C)** **HARD on `bears_value` `RECONCILIATION`+`TERMINAL_ONCE`** invariants, **advisory** on the rest, with an **owner-signed quarantine-manifest override** (the §5.2 dry-run + SF-g signed-disposition pattern) | **(C).** A genuine owner-only call — the cutover data-loss-vs-blocking-risk tradeoff, near-irreversible either way (a bad cutover on corrupt money, or a blocked cutover on a false positive). Money/settle correctness hard-gates; everything else is advisory; the override keeps a real false-positive from stranding the program. **Options+recommendation only.** | owner call |
| ▹ **Q3** | **Repair `actor_type` — reuse `backfill` vs a distinct `invariant_repair` actor.** | **(A)** reuse `backfill` (already in the frozen scripted-bypass set §②.3 — zero authority-surface change) · **(B)** add a reserved `actor_type="invariant_repair"` for forensic filterability (extends the §②.3 scripted set by one) | **(A) for v1** (zero change to K6 authority), with **(B) as an optional-additive forensic improvement** — a distinct actor makes "which mutations were sweep-driven?" a one-filter query. **Decide-able by design; flagged.** (B) touches the K6 scripted-bypass set → owner-gated if taken. | design default |

---

## 5. RETIREMENT MAP

| Row (FJ §2 L / §4 gap / §6 owner-queue) | How this dossier retires it | Status |
|---|---|---|
| **FJ §4 #7 — production data never audited or repaired; CUT-2 inherits corrupt rows** | The whole dossier: declared invariants + always-on report-only sweep (§2.1–2.4) closes the "never audited/repaired" leg; the CUT-2 verify-import stage 3.5 + stop-codes + scoreboard (§2.5) closes the "inherits corrupt rows" leg. | **CLAIMED / CLOSED** |
| **L-1 — the corrupt-row pattern this must catch** | **Co-owned with 09.** 09 closes the **version-drift leg** (`row.version != payload_version ⇒ refund`). I close the **live-residue leg** (`row.version == payload_version` but content violates an invariant — the double-fire residue 09's step-0 resumes untouched, §0). Different mechanism, same L-row. | **CLAIMED (live-residue leg; version-drift leg = 09)** |
| **L-18 — backup/DR + verified-restore + rollback disposition** | **Verified-restore leg CLOSED:** "verified" := boots + dry-run sweep clean (§2.5). The **rollback-data-disposition** leg stays owner-queued (a T2 addition, §6). | **PARTIALLY CLOSED (verified-restore leg)** |
| **Owner-queue T2 (Q-0222 amendment, FJ §8) — "verify-import step between freeze and swap"** | Exactly the CUT-2 stage 3.5 + the two stop-codes + the two scoreboard lines (§2.5). | **CLAIMED / CLOSED** |
| **§5 residual gap 1 (#1693) — mutated even when the fix failed** | The repair path leaves a failed repair **quarantined, not half-applied** (`enforce` dispatch table, §2.2) — audited + idempotent, the deliberate improvement over the stopgap. Reinforces 09's identical stance on `compensation_ref` failure. | **CLOSED (reinforced)** |
| **Rubric class 11 (cost/quota) + 13 (security/abuse) — FJ §8** | The sweep is their **runtime enforcement arm** (repair budget = class 11; mass-corruption circuit-breaker = class 13). Feeds them; does not own the rubric edit. | **FEEDS (not owned)** |
| **FJ §4 #11 — ungoverned prod-data copies / retention in the proving pipeline** | The verify-import/verified-restore gate is where a restored snapshot's *correctness* gets a checkpoint; the snapshot's *retention/erasure lifecycle* is a separate privacy cut (rubric 12). | **ADJACENT (correctness checkpoint only; retention deferred, §6)** |

---

## 6. DEFERRALS (labeled)

| Deferral | Reason | Bound |
|---|---|---|
| **Retention / erasure lifecycle of restored snapshots** (FJ §4 #11) | Scope — a **privacy/retention** concern (rubric class 12), not data-*integrity*. The sweep gates a restore's *correctness*, not the copy's *lifetime*. | Pointer to the retention cross-cut; the verify gate is the hook it plugs into. |
| **Compensation-saga for a repair that itself needs multi-step rollback** | Out of the v1 corpus — identical bound to 09 §9 (A#26 "record without a saga engine"). | v1 quarantines + operator finding; `repair_ref` `WorkflowRef` is the forward seam. |
| **GLOBAL-scope / whole-DB single-pass invariants** | v1 sweeps **per-guild in bounded batches** (matches the shipped economy read shape, `economy.py` is per-guild) with the `max_actions_per_run` cap. | A cross-guild global-scan invariant is a later band with a throughput budget (mirrors 09's `max_catchup`/bounded-batch posture). |
| **Automatic invariant *discovery*** (inferring invariants from the schema) | Invariants are **declared, never inferred** — matches §2.9 "the manifest contains no logic" and the declared-not-inferred discipline. | v1 ships hand-declared `InvariantSpec`s for the `bears_value` stores (economy, escrow, karma, XP) the fence requires. |
| **Rollback-data disposition** (L-18 second leg) | The reverse-import / replay / declared-loss decision is owner-gated with rollback-window N. | Stays a T2 owner-queue addition (FJ §3/§6); this dossier closes only the verified-restore leg. |

All deferrals sit behind a designed seam; none blocks building the grammar, the report-only sweep lane,
or the verify-import stage now.

---

## 7. Architecture rules honored (cited)

- **All repairs through the domain `*_mutation.py` seam + `emit_audit_action`** — a repair is a K7
  `WorkflowRef` (`run_ref` → `emit_central_audit` → `emit_audit_action`, `audit_events.py:52`); the fence
  §2.3 rejects a bare-`HandlerRef` repair. The sweep **never** writes a domain row itself.
- **All DB access via `utils.db.*` / `sb/kernel/db/*` (asyncpg only)** — `check_ref` reads and the
  `sb_quarantine`/`sb_invariant_sweep_log` CRUD live behind the db boundary; no raw `pool.execute` from
  the kernel sweep (unlike the shipped `automation_scheduler._fetch_due_rules` violation 09 §12 retires).
- **`services` must NOT import `views`; cogs never import cogs** — `sb/kernel/invariants/*` is kernel
  tier: imports `sb/spec/*`, `sb/kernel/db/*`, `sb/kernel/workflow/*` (K7), `sb/kernel/scheduler/*` (09);
  imports no view, no cog. Recovery/repair logic moves **out of** cog code into the kernel (a layering win).
- **`settings_keys` constants, never raw env** — the sweep cadence + `enforce` flags are `InvariantSpec`
  fields (manifest data) / `ConfigSpec` (vocab ⑥), never `os.getenv`.
- **INV-F/G/K preserved** — the `xp.coins`==Σ`economy_audit_log` reconciliation is INV-F territory; its
  `repair_ref` flows through the audited economy `CompoundOpSpec` (07 escrow/economy family), keeping
  every coin movement inside one audited txn. `InvariantSpec.invariant_id` is a **distinct** namespace
  axis (`data_invariant`) from `StoreSpec.invariant_tag` (the sole-writer AST fence) — no overload.

---

## 8. Seam corrections (flagged; source-wins Q-0120)

1. **Vocab §④.2's "three sites" table is non-exhaustive — additive, not wrong.** It enumerates dispatch
   dedup, confirm re-entry, and leg/relay dedup as the `IdempotencyKey` application sites. Spec 09
   already added a **4th** (the `{table}.version_reject:{...}` guard) without flagging it; my sweep-repair
   is a **5th** (`{invariant_id}.repair:{row_id}:{fingerprint}`), constructed identically. Flagged so a
   builder does **not** read the list as closed (that misread is exactly the drift the vocab exists to
   kill). The contract shape is unchanged; only the site inventory grows. **No divergence — a
   completeness note on ④.2.**
2. **No `Surface` member fits a sweep-repair's error classification.** `from_exception` (①) takes
   `surface`; a repair/compensation exception has no natural surface. 09 hit the same wall for scheduler
   fires and proposed `surface="scheduler"` as optional-additive. I extend that: `surface="maintenance"`
   (covering scheduler fires *and* sweep repairs) is the cleaner single addition — flagged as an
   optional-additive `Surface` member, consistent with 09's proposal. **Not a conflict; a shared naming
   gap the vocab left for the maintenance-lane consumers to name.**

*Written 2026-07-04 against the frozen shared vocabulary (`../shared-vocabulary.md`, all-five-pass) and
the two written strand-2 siblings (`../strand-2-runtime-durability/07-workflow-engine.md`,
`09-scheduler-state.md`). Spot-verified against shipped source this session:
`cogs/rps_tournament/_persistence.py:65-115,251-270`, `services/audit_events.py:52`,
`utils/db/economy.py:98,200-215`, `services/economy_service.py:254`. **NOT SOURCE OF TRUTH for
runtime** — a Phase-B design contract for the strand-3 cross-cutting build to execute against.*
