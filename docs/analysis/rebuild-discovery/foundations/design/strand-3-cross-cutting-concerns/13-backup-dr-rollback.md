# Strand-3 · Cross-Cutting Concern (d) — Backup / DR surviving cutover + rollback-data disposition — Buildable Design Spec

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B design contract. Precedence: shipped source &
> merged PRs (Q-0120) > the five strand-1 specs (for shapes they own) > the frozen
> `shared-vocabulary.md` > the written strand-2 siblings (`07`, `08`, `09`) > the written strand-3
> sibling (`11`) > this doc. This dossier **closes one never-surfaced foundational concern to design
> depth**: *the sole backup layer is an old-repo, self-labeled-UNVERIFIED, repo-bound CI workflow
> that will not follow the new repo; there is no gate proving a restore actually works for the new
> ledger-of-record; and **rollback destroys every post-cutover write** — no reverse importer, no
> replay log, no declared data disposition for the N-day window* (FJ `final-judgment-fable5-2026-07-03.md`
> **L-18** · §4 #2 · §6 owner-queue T2 "rollback-data disposition").
>
> **Consumes the FROZEN vocabulary + siblings — never redefines them:** the **config/data-plane
> rail** (⑥ `assert_data_plane`, the 4th kernel rail — the restore target is structurally
> `test`-plane, §2.2); the **audit spine** (`07-workflow-engine.md` `audit_log`, `mutation_id` PK,
> `prev_value`/`new_value`/`occurred_at` — the append-only change record I reuse as the replay-log
> substrate, §2.4); the **outbox** (`08-event-outbox.md` `AT_LEAST_ONCE`, `event_outbox`); the
> **`StoreSpec` grammar** (design-spec §2.8 — `table`/`sole_writer`/`retention`/`invariant_tag`, plus
> the `bears_value` value-bearing facet dossier 11 §2.1 formalizes) and **SF-g's REQUIRED-`disposition`
> pattern** (vocab §⑧, `store_retirements.yml`); and **dossier 11's "verified restore" definition**
> (`11-data-integrity-repair.md` §2.5: *a restore is "verified" iff it boots AND the dry-run invariant
> sweep passes against it*) — I **port the backup that feeds that definition** and make the proof
> **continuous**. Design against frozen decisions Q-0219…Q-0237 — never re-decided here.
>
> **Spot-verified against shipped source / frozen siblings this session** (load-bearing seams only,
> per method): `.github/workflows/backup-db.yml` **read in full** — repo-bound guard `if:
> github.repository == 'menno420/superbot'` (:56), repo-scoped secret `DATABASE_PUBLIC_URL` (:61),
> daily+monthly tiers (:31-37), the `>=10 CREATE TABLE` **liveness** floor (:119-124), the
> self-labeled `UNVERIFIED … delete if it proves unreliable` header (:23-26); design-spec **§5.2**
> (:1315-1351, one-way forward importer + rollback topology "old worker against its **untouched**
> database for a bounded window") and **§5.4** (:1367-1381, the 5-step migration shape + shadow
> scoreboard "read-off, not a feeling"); the `audit_log` DDL (`07` :250-264) and `event_outbox`
> (`08` §3.2). Source wins.

---

## 0. The boundary — what is already designed vs the genuine gap (anti-pad — read first)

**Already designed (one line each; this dossier does NOT re-derive these):**

- **The backup workflow exists** — `backup-db.yml` daily+monthly `pg_dump` → GitHub-artifact, `>=10
  CREATE TABLE` integrity floor, failure-issue. *It just does not survive the repo change and was
  never restore-proven.*
- **The rollback topology is fixed** (design-spec §5.4): importer reads the **OLD** (frozen) DB →
  writes the **NEW** DB; cutover flips the new bot live on the NEW DB; the OLD DB stays untouched;
  rollback = re-deploy the old worker on that OLD DB. *What happens to the NEW DB's post-cutover
  writes on rollback is undesigned.*
- **The shadow scoreboard exists** (§5.4): cutover-exit criteria are scoreboard read-offs. *It has no
  backup-health line and no rollback-data-cost line.*
- **"Verified restore" is already defined** — dossier 11 §2.5: *boots + dry-run invariant sweep
  clean.* I **consume this verbatim**; my job is the backup that feeds it, the RPO, and making the
  proof continuous — **not** re-defining "verified."

**The genuine gap this dossier owns (all depth goes here):** (1) the backup **ported** into the new
repo (de-repo-bound, secret re-created, graduated out of UNVERIFIED); (2) an **RPO target** with a
tiered source; (3) the verified-restore proof made **continuous + a CUT gate** (not a one-time manual
check); and (4) the **rollback-data disposition** — reverse-import / replay-log / declared-loss,
**tiered by round-trippability**, with the `rollback_class` fence and window N. Leg (4) is exactly
the leg dossier 11 explicitly **deferred to me** ("Rollback-data disposition (L-18 second leg) … this
dossier closes only the verified-restore leg", 11 §6).

---

## 1. THREAT / FAILURE MODEL

The failure mode of a backup/DR layer is **absence, not error** — nothing goes red, the gap is
silent, and the first real test is during the incident. Six concrete scenarios, grounded in source.

| # | Scenario (who / what / how) | Grounded in | Blast radius |
|---|---|---|---|
| **T-1** | **Portability cliff — the backup does not follow the new repo.** `backup-db.yml` is gated `if: github.repository == 'menno420/superbot'` (:56) and reads a **repo-scoped** secret `DATABASE_PUBLIC_URL` (:61). The new repo starts with **zero backup coverage** until someone re-ports the workflow, re-creates the secret, and raises the 400-day retention setting — three manual steps with no failing signal if skipped. | `backup-db.yml:56,61`; prod-deploy §Backups one-time setup | The new **ledger-of-record** (money/audit spine) runs **unbacked** for an unknown window; a data-loss event during it has RPO = ∞. Silent because the failure mode is *nothing runs*. |
| **T-2** | **Schrödinger's backup — UNVERIFIED, never restore-tested.** The workflow self-labels `UNVERIFIED … Delete or disable this workflow if it proves unreliable` (:23-26). Its integrity check is `>=10 CREATE TABLE` (:119-124) — a **liveness** floor (the dump isn't empty), **not** a restorability proof. A subtly-broken dump (encoding, a truncated large table, a missing role/extension on the restore target) passes the 10-table floor and uploads as a "backup." | `backup-db.yml:23-26,119-124`; L-18 "self-labeled UNVERIFIED" | False confidence: the DR layer is unproven until a real restore is attempted, and by construction the **first real attempt is during an incident**. |
| **T-3** | **RPO undefined for the ledger-of-record.** Daily `pg_dump` ⇒ up to **~24 h** of writes unrecoverable on any restore-from-backup. No RPO number is stated anywhere for a bot whose reason to exist is the money/audit spine. | `backup-db.yml:31-32` (daily cron); prod-deploy §Backups | On any restore, up to a day of **economy ledger + audit history** silently gone; the operator's "where did these coins come from?" is unanswerable for the lost window; unbudgeted and unmeasured. |
| **T-4** | **Rollback destroys the N-day window (the core gap).** Per §5.4 the new bot writes only the **NEW** DB after cutover; the OLD DB is frozen; rollback re-deploys the old worker on that OLD DB. So **every write made through the new bot during window N lives only on the NEW DB** and vanishes the instant the old bot (authoritative again) resumes on the OLD DB. No reverse importer, no replay log, no declared-loss policy exists. | §5.4 :1349-1351; L-18 "rollback destroys all post-cutover writes"; FJ §4 #2 | The **safety lever itself** silently deletes N days of real user state — economy transactions, XP, tickets opened, mod actions, giveaways — across **every** production guild. *"A rollback lever whose data cost is unstated is not a safety lever."* |
| **T-5** | **Reverse-import is structurally impossible for new-only writes.** The rebuild **collapses** schema (§5.1: session state → checkpoints; renamed/dropped tables; the whole point is to shed fragmentation). A write from a new-bot-only command, or into a collapsed checkpoint, has **no old-schema table to reverse into**. Only the name-stable ledger/aggregate tables (`economy_audit_log`, XP, karma — §5.2 "import name-stable where cheap") can round-trip. | §5.1-5.2; design-spec decision 8 | Any disposition that *promises* full recovery is a lie by construction; the honest design **must** declare the un-round-trippable classes as loss — which forces the owner-gated call, not a silent default. |
| **T-6** | **The verify-restore job needs prod-like infra the CI lacks, and must never touch prod.** A verified-restore must restore into a real Postgres and boot the bot — the **same** Postgres-service-container gap already flagged for `golden-parity` (design-spec §6 linchpin: "this repo's own `code-quality` workflow runs no Postgres service container"). And the restore target's DSN **must** be forced `SB_DATA_PLANE=test` (vocab ⑥) so a verify-restore can **never** open or clobber prod. | design-spec §6 (linchpin); vocab ⑥ `assert_data_plane` | Without the plane rail, a mis-wired verify job could point a restored dump's DSN at prod; with it, structurally impossible (`RefuseBoot` before any network I/O). Infra cost is shared with `golden-parity`, not net-new. |

**The through-line:** T-1/T-2/T-3 are the **backup layer's own** decay (portability, unproven,
un-budgeted RPO) — a permanent CI proof fixes all three. T-4/T-5 are the **rollback-data** gap — a
declared, tiered, bounded disposition fixes it, and T-5 is *why* it must be owner-gated rather than
auto-defaulted. T-6 is the **safety envelope** the proof machinery must satisfy (prod-like infra,
plane-forced). One backbone answers all three shapes.

---

## 2. DESIGN RESPONSE

One backbone: **the backup becomes a first-class ported artifact with a *continuous* verified-restore
proof, a stated RPO, and a declared, bounded, tiered rollback-data contract.** Buildable depth on the
port + CI proof + the `rollback_class` grammar/fence; decision-ready depth on the three postures (§4).

### 2.1 Port the backup as a first-class new-repo artifact (de-repo-bind) — *decide-able by design*

- **Drop the repo-identity guard.** `if: github.repository == 'menno420/superbot'` (:56) becomes an
  input-driven guard (`vars.BACKUP_ENABLED`) or is removed — the new repo owns its own copy; the guard
  was a fork-safety relic, not a DR property.
- **Re-create the secret as a named cutover step.** `DATABASE_PUBLIC_URL` is added to the new repo's
  Actions secrets — this is a line item in the **cutover runbook** (interlocks with FJ §4 #10
  credential lifecycle; I *name* the one-time re-creation, the rotation contract is a separate cut, §6).
- **Graduate out of "UNVERIFIED."** The `delete if it proves unreliable` self-label (:23-26) is
  replaced by the continuous proof in §2.2 — the header's own precondition ("confirm … the dump is
  restorable") is finally *mechanized* rather than left to a human's one-time memory.
- **Rename the integrity floor's comment** to state it proves **non-empty, not restorable** (:119-124)
  — a trivial honesty fix so no reader mistakes the liveness floor for a restore proof (the exact
  Q-0120 "a green that contradicts evidence" trap).
- Keep the daily + monthly tiers, the failure-issue, and the PGDG-client install verbatim — they are
  correct; only the repo-binding and the verification story change.

### 2.2 The continuous verified-restore proof — CONSUMES dossier 11's definition (I add cadence + source + plane)

A new scheduled workflow `restore-verify.yml` (kernel-band CI, not a PR-required check — a
**reliability job**):

> download the **latest backup artifact** → restore into a **fresh Postgres service container**
> (shared infra with `golden-parity`, T-6) whose DSN is **forced `SB_DATA_PLANE=test`** (vocab ⑥
> `assert_data_plane` ⇒ structurally cannot be prod) → **boot the new bot to readiness 200** → run the
> **dry-run invariant sweep** (dossier 11 §2.5) → **green iff boots AND sweep-clean.**

- This is **exactly dossier 11's "verified := boots + dry-run sweep clean"**, run *on a schedule
  against the real artifact* instead of once, by hand, at setup. I **consume** the definition; I own
  only the **cadence** (weekly ≥ backup cadence), the **artifact source** (the latest daily dump), and
  the **plane-forced target** (⑥). No new definition of "verified."
- **Fixes T-1 + T-2 together:** a job that restores the *new-repo* artifact weekly *is* the proof the
  backup both exists and works — the failure mode flips from silent-absence to a red CI job + a
  failure-issue (reusing the workflow's existing issue-on-failure pattern).
- **The `last_verified_restore_age` metric** it emits is the backup-health signal §2.5 puts on the
  scoreboard and §2.3 reads as the RPO witness.

### 2.3 The RPO contract — a stated number + a tiered source (fixes T-3)

State an explicit RPO, tiered by store value-class rather than one flat number:

| Tier | Store class (keyed on `StoreSpec.bears_value` / `invariant_tag` INV-F/G/K) | RPO source | RPO |
|---|---|---|---|
| **Ledger/audit** | `bears_value=True` — `economy_audit_log`, XP, karma, treasury, the `audit_log` spine | the **append-only audit spine** (`07` `audit_log`, `mutation_id` PK, `occurred_at`) IS a continuous change log — money/audit state is reconstructable to the outbox-flush cadence, far tighter than the daily dump | **≤ outbox-flush cadence (minutes)** for reconstructable money/audit state |
| **Everything else** | non-value stores, checkpoints, presets, bindings | the daily `pg_dump` floor | **≤ 24 h** (the current pg_dump window) |
| **(optional)** | whole-DB point-in-time | Railway PITR (Pro-plan-gated; already flagged railway-setup-plan §6 R2) | **≈ minutes**, if the plan is upgraded (owner call) |

The insight: the money/audit spine's **RPO is already near-continuous for free** because the audit
log is append-only and captures `prev_value`/`new_value` per mutation — the daily dump is the *floor*,
not the *ceiling*. The RPO **number** and whether to buy Railway PITR are the owner call (§4 Q1).

### 2.4 The rollback-data disposition — a declared, bounded, tiered contract (fixes T-4/T-5)

The core mechanic. Three moves:

**(a) The window's writes are already forensically captured — reuse, don't rebuild.** Every
post-cutover auditable mutation is *already* an append-only row in the `audit_log` spine (`07`) +
`event_outbox` (`08`), keyed by `mutation_id`, with `prev_value`/`new_value`/`occurred_at`. The
N-day window's writes are therefore **not unrecoverable *data*** — they are unrecoverable **into the
old schema**. The "replay log" the concern asks for **already exists**; the design question is what to
*do* with `audit_log WHERE occurred_at >= cutover_freeze_ts` on rollback.

**(b) A new REQUIRED `StoreSpec.rollback_class` — tiered by round-trippability** (mirrors SF-g's
REQUIRED-`disposition`, vocab §⑧ / §⑧-fork-8; a *different axis* — SF-g disposes a store **dropped at
migration**, this disposes a live store's **writes stranded at rollback**):

```python
class RollbackClass(StrEnum):
    REVERSE_IMPORTABLE = "reverse_importable"  # name-stable ledger/aggregate — the delta round-trips to OLD schema
    DECLARED_LOSS      = "declared_loss"       # new-only / collapsed / renamed — no old home; loss is DECLARED + signed
    REPLAY_INTENT      = "replay_intent"       # audit rows kept as a human-reviewed replay list (later band, §6)
# on StoreSpec:
    rollback_class: RollbackClass              # [S] REQUIRED — no default (SF-g pattern: an unstated data cost is a bug)
```

| Class | Which stores | On rollback |
|---|---|---|
| `REVERSE_IMPORTABLE` | the §5.2 name-stable ledger/aggregate tables (`economy_audit_log`, XP, karma) — the only ones with an old-schema home | a **narrow reverse importer** (`tools/importer/reverse/`, the §5.2 importer's mirror) maps the post-cutover delta back to OLD schema — bounded to these tables only |
| `DECLARED_LOSS` | new-only features, collapsed session→checkpoint state, renamed/dropped tables (T-5: **structurally cannot** round-trip) | writes are **explicitly declared lost**; the owner signs a **loss manifest** (row counts by store); users are notified (interlocks with the FJ §4 #9 comms/ring plan) |
| `REPLAY_INTENT` | *(optional, deferred §6)* value-bearing rows worth a manual second look | the `audit_log` slice becomes a **human-reviewed** replay list — never auto-replayed (the command surface changed: renames/D-5 drops make automated command replay unsafe) |

**(c) Make N small and the posture forward-fix-first, so DECLARED_LOSS is cheap by construction.**
The default response to a post-cutover bug is a **hotfix forward**, not a rollback; rollback is the
last resort. Combined with the **progressive-exposure ring** (FJ §6 T3: volunteer guilds before the
full swap) and a **short N**, the number of guilds × days at risk — and thus the DECLARED_LOSS blast
radius — is bounded *before* the disposition even fires. The **value of N** is the owner carry
(Stage-3, Tier-3 line 359); the **mechanism** is designed here.

**The rollback playbook (a written CUT-3 artifact):** rollback decision → freeze new bot → export
`audit_log` delta since `cutover_freeze_ts`, partitioned by `rollback_class` → reverse-import the
`REVERSE_IMPORTABLE` tier into the OLD DB (audited, idempotent — reuses the §5.2 importer's upsert-by-
natural-key + stop-codes) → emit the `DECLARED_LOSS` loss-manifest for owner sign-off → re-deploy old
worker → notify guild admins. The playbook lands beside the §5.4 migration shape.

### 2.5 The fence + the scoreboard hooks (so it cannot evaporate — V-3)

- **`rollback_class_declared` compile fence** (`manifest-validate`, §6 required check #2, beside
  `leaderboard-has-writer`): every `StoreSpec` **MUST** carry a `rollback_class` ⇒ else
  `SEMANTIC_VIOLATION ("rollback_class_undeclared")` → CI-red. *This is the structural fix for T-4:
  you cannot ship a store whose rollback-data cost is unstated.* Same one-way-door as SF-g's signed
  `disposition`.
- **Two new §5.4 shadow-scoreboard lines**, so "the data cost of rolling back *right now*" is a
  **read-off, not a feeling** (the §5.4 posture, extended from cutover-exit to rollback-cost):
  - `rollback_window_writes_by_class` — live count of post-cutover `audit_log` rows in each
    `rollback_class` (how much is at risk, and how much of it is REVERSE_IMPORTABLE vs DECLARED_LOSS).
  - `last_verified_restore_age` — the §2.2 backup-health / RPO witness (a stale value = the backup
    proof is failing = do not cut over).
- **The verified-restore CUT gate** (consuming dossier 11's definition): cutover cannot proceed unless
  the **most recent `restore-verify.yml` run is green** — whether HARD or advisory is owner-gated (§4 Q2).

---

## 3. LANDING SITE (so it cannot evaporate — V-3)

| Response | Lands as | Concrete home |
|---|---|---|
| Port + de-repo-bind the backup (§2.1) | **Ops/CI artifact in the new repo** + a named cutover-runbook step | new-repo `.github/workflows/backup-db.yml` (guard dropped); cutover runbook (secret re-creation) |
| `restore-verify.yml` continuous proof (§2.2) | **A scheduled reliability CI job** (Postgres-service container, plane-forced) — *not* a PR-required check | new-repo `.github/workflows/restore-verify.yml`; consumes dossier 11 §2.5 sweep + shares `golden-parity`'s Postgres-service infra (design-spec §6 linchpin) |
| RPO contract + tiered source (§2.3) | **A stated RPO in the design spec** + Stage-3 consolidation line | design-spec §5 (RPO number); the ledger tier reuses the `07` `audit_log` spine |
| `RollbackClass` enum + REQUIRED `StoreSpec.rollback_class` (§2.4b) | **Gate-0 grammar field** on `StoreSpec` (§2.8), sibling to `retention`/`invariant_tag`/`bears_value` | new value in `sb/spec/...` StoreSpec; SubsystemManifest export |
| `rollback_class_declared` fence (§2.5) | **`manifest-validate` CI gate** (§6 required check #2), beside `leaderboard-has-writer` | manifest compiler fence |
| Narrow reverse importer for the REVERSE_IMPORTABLE tier (§2.4) | **The §5.2 importer's mirror** (`tools/importer/reverse/`), built + golden-tested against a snapshot fixture, same discipline as the forward importer | design-spec §5.2 (importer family); the rollback playbook |
| Rollback playbook (§2.4c) | **A written CUT-3 artifact** beside the §5.4 migration shape | design-spec §5.4; CUT-3 gate list |
| Verified-restore CUT gate + 2 scoreboard lines (§2.5) | **CUT-3 gate** + **§5.4 compat-scoreboard** lines | design-spec §5.4 (scoreboard); Stage-3/CUT-3 gate list |
| The whole DR posture as a reliability lens | **Rubric class 13** (reliability/security non-functional — dossier 10) — DR is a class-13 probe | rubric §8 (owned by dossier 10; I *feed* it) |

---

## 4. OWNER-GATED

| # | Decision | Options | Recommendation | Gate |
|---|---|---|---|---|
| 🔒 **Q1** | **RPO target + source tier.** *(the concern's "RPO the backup must meet")* | **(A)** daily `pg_dump` only — flat RPO ≤ 24 h · **(B)** daily floor **+** audit-spine-derived near-continuous RPO for `bears_value` ledger/audit stores (§2.3) · **(C)** (B) **+** Railway PITR (RPO ≈ minutes, whole-DB) — requires a plan upgrade | **(B)**, with **(C)** if/when the plan is upgraded. The money/audit spine's tight RPO is **already free** from the append-only `audit_log` (`07`); the daily dump stays the floor for everything else. PITR is pure plan-cost-vs-value (already flagged railway §6 R2). **A genuine owner call — the plan-cost / data-value tradeoff — options+recommendation only.** | owner call (plan cost) |
| 🔒 **Q2** | **Verified-restore as a HARD CUT-3 gate vs advisory.** *(the concern's "verified-restore a HARD CUT-3 gate?")* | **(A)** HARD — cutover blocked unless the latest `restore-verify.yml` is green · **(B)** advisory scoreboard line only (`last_verified_restore_age`) | **(A).** A backup you have never proven restorable is not a backup (T-2); and because §2.2 makes the proof **continuous**, the gate is almost always already green, so HARD rarely *blocks* — it only catches the real "the backup silently broke" case at the one moment it matters. The CLAUDE.md "a check can lie" caveat is answered by the sweep-clean definition being the *same* one dossier 11 runs at import. **Decide-able against the recommended default; flagged because the concern marks it owner-gated.** | owner posture |
| 🔒 **Q3** | **Rollback-data disposition + window N.** *(the concern's core owner call — "reverse-import / replay-log / declared-loss + window N")* | **(A)** pure DECLARED_LOSS + short N + owner sign-off (cheapest; loses the window's money rows too) · **(B)** DECLARED_LOSS **+ a narrow reverse-import valve for the `REVERSE_IMPORTABLE` ledger/audit tier** + short forward-fix-biased N + owner-signed loss manifest · **(C)** full reverse-import of everything — **rejected**: structurally impossible for new-only / collapsed stores (T-5) | **(B).** Full recovery is a lie by construction (T-5), so the honest design is: **round-trip the one class where loss is unacceptable (real money/audit — it round-trips name-stable per §5.2), declare the rest lost, keep N short and forward-fix-first so the declared loss is small.** The **value of N** stays the owner carry (Stage-3, Tier-3). **A genuine owner-only call** — a data-loss policy with a real reverse-importer build cost; near-irreversible either way (lost user state, or an over-built reverse path that will rarely fire). **Options+recommendation only.** | owner call (data-loss policy + N) |
| ▹ **Q4** | **De-repo-bind mechanics + the integrity-floor comment fix (§2.1).** | **(A)** drop the `github.repository` guard, re-create the secret, rename the `>=10 CREATE TABLE` comment to "non-empty, not restorable" · **(B)** keep the guard parameterized on a repo var | **(A)** — contained, reversible, test-covered by §2.2's continuous proof. **Decide-able by design; flagged.** | design default |

---

## 5. RETIREMENT MAP

| Row (FJ §2 L / §4 gap / §6 owner-queue) | How this dossier retires it | Status |
|---|---|---|
| **L-18 — backup/DR doesn't survive cutover; no verified-restore gate; rollback destroys post-cutover writes** | **All three legs.** Backup-survives-cutover: **CLOSED** (§2.1 port + de-repo-bind). Verified-restore gate: **CLOSED** (§2.2 continuous CI proof consuming dossier 11's definition + §2.5 CUT-3 gate) — completes what dossier 11 left PARTIAL (11 defined "verified"; I port the backup that feeds it, make the proof continuous, and land the gate). Rollback-data disposition: **CLOSED** (§2.4 declared tiered contract + `rollback_class` REQUIRED fence + reverse-import valve + playbook). | **CLAIMED / CLOSED** (verified-restore leg **co-owned with 11**) |
| **FJ §4 #2 — "Rollback destroys post-cutover data / backup-DR doesn't survive cutover"** (the ★ completeness gap = L-18) | Same as L-18; this is its §4 entry. | **CLAIMED / CLOSED** |
| **FJ §6 owner-queue T2 addition — "Rollback-data disposition: reverse-import / replay log / declared-loss sign-off?"** (line 365, stress-D-3 + critics) | Exactly §2.4 (the tiered `rollback_class` contract) + **Q3** (the owner call with options+recommendation). | **CLAIMED** (mechanism designed; the posture is Q3) |
| **FJ §6 Tier-3 carry — "CUT-3 rollback window N set at Stage 3"** (line 359) | The **mechanism** that gives N meaning is designed (§2.4c — N governs the DECLARED_LOSS blast radius, read off `rollback_window_writes_by_class`); the **value of N** stays the owner's Stage-3 carry. | **PARTIALLY CLOSED** (mechanism closed; N-value = owner) |
| **RPO target** (implied by L-18; the concern's second owner question) | §2.3 states an explicit tiered RPO; **Q1** is the owner call on the number + PITR. | **CLAIMED** (contract stated; number = Q1) |
| **FJ §4 #9 — no user-facing change-communication mechanic** | The DECLARED_LOSS **loss-manifest → guild-admin notification** interlocks with the comms/ring plan; I **FEED** the hook (the notification trigger), do not own the comms plan. | **FEEDS (not owned)** |
| **FJ §4 #10 — credential lifecycle** (the `DATABASE_PUBLIC_URL` secret) | I **name** the one-time secret **re-creation** as a cutover-runbook step (§2.1); the rotation/revocation/compromise contract is a separate credential cut. | **ADJACENT (re-creation named; rotation deferred, §6)** |
| **Rubric class 13 (reliability/security non-functional) — FJ §8 / dossier 10** | The DR posture (backup-health, verified-restore, rollback-cost read-off) is a **class-13 probe surface**; I feed it, dossier 10 owns the rubric edit. | **FEEDS (not owned)** |

---

## 6. DEFERRALS (labeled)

| Deferral | Reason | Bound |
|---|---|---|
| **The value of window N** | Owner-gated data-loss policy (Q3); a Stage-3 / CUT-3 carry (FJ Tier-3 line 359). | The mechanism (§2.4c) is designed and reads N off `rollback_window_writes_by_class`; only the number is deferred. |
| **`REPLAY_INTENT` — automated command-level replay** | The command surface **changed** (Q-0224 renames, D-5 drops), so auto-replaying a window's mutations as commands is unsafe. | v1 = a **human-reviewed** replay list from the `audit_log` slice; the enum member is reserved so the later band slots in with zero grammar change. |
| **Full reverse-import of new-only / collapsed stores** | **Structurally impossible** (T-5) — the rebuild sheds schema; these rows have no old-schema home. | Not a build deferral — a declared reality: `DECLARED_LOSS` is the *honest* disposition, signed by the owner, bounded by a short N. |
| **Railway-native PITR** (RPO ≈ minutes) | **Plan-gated** — an owner cost decision already recorded (railway-setup-plan §6 R2). | Q1 option (C); the `pg_dump` + audit-spine tiers stand alone without it. |
| **Credential rotation / revocation / compromise-recovery** for `DATABASE_PUBLIC_URL` / token / DSN (FJ §4 #10) | Scope — a **credential-lifecycle** cut, not backup/DR. | I name the one-time re-creation; the lifecycle contract is a separate cross-cut. |

All deferrals sit behind a designed seam; none blocks porting the backup, building the continuous
verified-restore proof, adding the `rollback_class` fence, or writing the rollback playbook now.

---

## 7. Architecture rules honored (cited)

- **All DB access via `utils.db.*` / `sb/kernel/db/*` (asyncpg only)** — the reverse importer and the
  restore-verify boot read/write only through the db seam; the restore target is a *separate* Postgres,
  never a raw `pool.execute` against prod. The verify job's DSN is **forced `SB_DATA_PLANE=test`**
  (vocab ⑥ `assert_data_plane`), so it structurally cannot open prod.
- **All auditable mutations through the audited seam** — the reverse importer's writes into the OLD
  DB are the §5.2 importer discipline (upsert-by-natural-key, stop-codes, owner-reviewed dry-run); the
  post-cutover delta it reads **is** the `audit_log` spine (`emit_audit_action`, `07` `audit_log`), so
  every reversed row is already a forensic record. No disposition mutates state silently.
- **`services` must NOT import `views`; cogs never import cogs** — none of this touches cog/view code;
  it is CI workflows (`backup-db.yml`, `restore-verify.yml`), the `tools/importer/` family, a
  `StoreSpec` grammar field, and a manifest fence — all outside the runtime layer table.
- **`settings_keys` constants / `ConfigSpec`, never raw env** — the backup DSN, RPO cadence, and N are
  config/spec fields (`DATABASE_PUBLIC_URL` a repo secret, `rollback_class` a `[S]` StoreSpec field, N a
  Stage-3 config value), never scattered `os.getenv`.
- **Report-only / one-way-door discipline (CLAUDE.md adopt-with-a-kill-switch)** — the verified-restore
  proof *reports* (a red CI job + issue) before it can *gate* (Q2); DECLARED_LOSS requires an explicit
  **owner signature**, never a silent auto-drop — the same signed-disposition rail as SF-g and dossier
  11's quarantine manifest.

---

## 8. Seam corrections (flagged; source-wins Q-0120)

1. **`StoreSpec` field inventory is additive, not closed.** Design-spec §2.8 line 866 enumerates
   `StoreSpec` as `table`/`sole_writer`/`retention`; §5.3 adds `invariant_tag`, §1560 adds
   `checkpoint_class`, dossier 11 §2.1 adds `bears_value`. My `rollback_class` is the next additive
   `[S]` facet on the same primitive — flagged so a builder does **not** read the §2.8 list as closed
   (that misread is the drift the grammar exists to kill). **No divergence — the field set grows; the
   primitive is unchanged.**
2. **SF-g's `disposition` and my `rollback_class` are sibling axes, not the same field.** SF-g (vocab
   §⑧ fork-8) disposes a store **dropped at migration** (`export`/`reverse-migrate`/`declared-loss` on
   `store_retirements.yml`); `rollback_class` disposes a **live** store's **writes stranded at
   rollback**. I deliberately **align the vocabulary** (`reverse_importable`≈`reverse-migrate`,
   `declared_loss`≈`declared-loss`) so the two read consistently, but they are **distinct axes** on
   distinct boundaries. Flagged so neither is mistaken for the other. **Consistent-with-skeleton, not a
   redefinition.**
3. **The concern's "replay-log" already has a substrate — the audit spine (`07` `audit_log`).** The
   task brief lists "replay-log" as a candidate rollback mechanism as if it must be built; it need not —
   the append-only `audit_log` (`mutation_id` PK, `prev_value`/`new_value`/`occurred_at`) **is** the
   post-cutover change record. Flagged so a builder reuses it rather than standing up a parallel log
   (the fragmentation the rebuild exists to shed). **A reuse note, not a conflict.**

*Written 2026-07-04 against the frozen shared vocabulary (`../shared-vocabulary.md`, all-five-pass),
the strand-2 siblings (`../strand-2-runtime-durability/07-workflow-engine.md`, `08-event-outbox.md`,
`09-scheduler-state.md`), and the strand-3 sibling (`11-data-integrity-repair.md`). Spot-verified
against shipped source / frozen siblings this session: `.github/workflows/backup-db.yml` (read in
full — `:23-26,31-37,56,61,119-124`), design-spec §5.2 (`:1315-1351`) / §5.4 (`:1367-1381`), `07`
`audit_log` DDL (`:250-264`), `08` `event_outbox` (§3.2), dossier 11 §2.5, prod-deploy §Backups
(`:213-278`). **NOT SOURCE OF TRUTH for runtime** — a Phase-B design contract for the strand-3
cross-cutting build to execute against.*
