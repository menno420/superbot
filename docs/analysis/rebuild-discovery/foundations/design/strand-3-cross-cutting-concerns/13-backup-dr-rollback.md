# Strand-3 · Cross-Cutting Concern (d) — Backup / DR surviving cutover + rollback-data disposition — Buildable Design Spec

> **NOT SOURCE OF TRUTH for runtime.** A Phase-B design contract. Precedence: shipped source &
> merged PRs (Q-0120) > the five strand-1 specs (for shapes they own) > the frozen
> `shared-vocabulary.md` > the written strand-2 siblings (`07`, `08`, `09`) > the written strand-3
> sibling (`11`) > this doc. This dossier **closes one never-surfaced foundational concern to design
> depth**: *the sole backup layer is an old-repo, self-labeled-UNVERIFIED, repo-bound CI workflow
> that will not follow the new repo; there is no gate proving a restore actually works for the new
> ledger-of-record; and **rollback destroys every post-cutover write** — no reverse importer, no
> replay log, no declared data disposition for the N-day window* (FJ `final-judgment-fable5-2026-07-03.md`
> **L-18** · §4 #2 · §6 owner-queue T2 "rollback-data disposition", line 365).
>
> **Consumes the FROZEN vocabulary + siblings — never redefines them:** the **config/data-plane
> rail** (⑥ `assert_data_plane`, the 4th kernel rail — the restore target is structurally
> `test`-plane, §2.2); the **audit spine** (`07-workflow-engine.md` `audit_log`, `mutation_id` PK,
> `prev_value`/`new_value`/`occurred_at` — the append-only change record I reuse as the *forensic*
> replay substrate, with the completeness caveat §2.4a); the **outbox** (`08-event-outbox.md`
> `AT_LEAST_ONCE`, `event_outbox`); the **`StoreSpec` grammar** — the **six base §2.8 fields**
> (`table`/`sole_writer`/`retention`/`checkpoint_class`/`invariant_tag`/`reader_domains`, design-spec
> §2.8 :866-869 — a **closed** six, verified) **plus spec 09's version-extension** (`bears_value` /
> `version_policy` / … on `sb/spec/versioning.py`, `09` :79/:191 — an *unratified Gate-0 proposal*, §8-1)
> — and **SF-g's REQUIRED-`disposition` pattern** (vocab §⑧, `store_retirements.yml`); and **dossier
> 11's "verified restore" definition** (`11-data-integrity-repair.md` §2.5: *a restore is "verified"
> iff it boots AND the dry-run invariant sweep passes against it*) — I **port the backup that feeds
> that definition** and make the proof **continuous + side-effect-free**. Design against frozen
> decisions Q-0219…Q-0237 — never re-decided here.
>
> **Spot-verified against shipped source / frozen siblings this session** (load-bearing seams only,
> per method): `.github/workflows/backup-db.yml` **read in full** — repo-bound guard `if:
> github.repository == 'menno420/superbot'` (:56), repo-scoped secret `DATABASE_PUBLIC_URL` (:61),
> daily (`:31-32`) + monthly 400-day (`:33-37`, `:131-139`) tiers, the **repo-artifact-retention clamp**
> (`:131-136` — 400→90 unless the repo max is raised), the `>=10 CREATE TABLE` **liveness** floor
> (`:119-124`), the self-labeled `UNVERIFIED … delete if it proves unreliable` header (:23-26);
> **design-spec §2.8 `StoreSpec`** (:866-869 — all six base fields declared **together**, `checkpoint_class:
> enum {ledger, aggregate, session}`); design-spec **§5.2** (:1315-1351 — one-way forward importer +
> the rollback topology "old worker against its **untouched** database for a bounded window", **the
> topology sentence lives at :1349-1351, the closing paragraph of §5.2**) and **§5.4** (:1367-1373, the
> **5-step** migration shape — step (4) `freeze old bot → final import delta → flip Railway`, step (5)
> the bounded rollback window; scoreboard :1375-1381 "read-off, not a feeling"); the golden-parity
> **fake-HTTP-over-real-discord.py-state-machine** harness (`parity/`, design-spec :1431-1435); the
> `audit_log` DDL (`07` :408-422 — columns `mutation_id/subsystem/mutation_type/target/scope/guild_id/
> prev_value/new_value/actor_id/actor_type/occurred_at/detail/correlation_id`; **no `table`/`store`
> column** — §2.5); `event_outbox` (`08` §3.2); spec 09's version-extended `StoreSpec` (`09` :79/:191).
> Source wins.

---

## 0. The boundary — what is already designed vs the genuine gap (anti-pad — read first)

**Already designed (one line each; this dossier does NOT re-derive these):**

- **The backup workflow exists** — `backup-db.yml` daily + monthly `pg_dump` → GitHub-artifact, `>=10
  CREATE TABLE` integrity floor, failure-issue. *It just does not survive the repo change, was never
  restore-proven, and its 400-day monthly tier is silently clamped to 90 unless a repo setting is raised.*
- **The rollback topology is fixed** (design-spec **§5.2** :1349-1351 — the topology sentence; **§5.4**
  :1367-1373 — the step sequence): the importer reads the **OLD** (frozen) DB → writes the **NEW** DB;
  cutover flips the new bot live on the NEW DB; the OLD DB stays untouched; rollback = re-deploy the old
  worker on that OLD DB. *(Attribution fix vs the earlier draft: the "importer reads OLD → writes NEW;
  rollback re-deploys the old worker on the OLD DB" statement is **§5.2** :1349-1351, not §5.4; §5.4 is
  the 5-step sequence whose step (4) is `freeze → final import delta → flip` and step (5) is the bounded
  rollback window — §8-4.)* **What happens to the NEW DB's post-cutover writes on rollback is undesigned.**
- **The shadow scoreboard exists** (§5.4 :1375-1381): cutover-exit criteria are scoreboard read-offs. *It
  has no backup-health line and no rollback-data-cost line.*
- **"Verified restore" is already defined** — dossier 11 §2.5: *boots + dry-run invariant sweep clean.* I
  **consume this verbatim**; my job is the backup that feeds it, the RPO, making the proof continuous, and
  making the verify-boot **side-effect-free** — **not** re-defining "verified."
- **`bears_value` is spec 09's, not mine and not the base grammar's** — it is a field on 09's
  *version-extended* `StoreSpec` (`sb/spec/versioning.py`, `09` :79/:191), an **unratified Gate-0
  proposal** that is *not* one of the six base §2.8 fields. My RPO tiering (§2.3) and `rollback_class`
  derivation (§2.4) read it; if it is renamed/rejected at Gate-0 they re-bind to whatever replaces it (§8-1).

**The genuine gap this dossier owns (all depth goes here):** (1) the backup **ported** into the new
repo (de-repo-bound, secret re-created, 400-day retention raised, graduated out of UNVERIFIED); (2) an
**RPO target** with a tiered source — *honestly costed* (§2.3 corrects the "free near-continuous money
RPO" error); (3) the verified-restore proof made **continuous, side-effect-free, and a CUT gate** (not a
one-time manual check); and (4) the **rollback-data disposition** — reverse-import / replay-log /
declared-loss, **tiered by a mechanically-derived `rollback_class`**, with the fence and window N. Leg
(4) is exactly the leg dossier 11 explicitly **deferred to me** ("Rollback-data disposition (L-18 second
leg) … this dossier closes only the verified-restore leg", 11 §6).

---

## 1. THREAT / FAILURE MODEL

The failure mode of a backup/DR layer is **absence, not error** — nothing goes red, the gap is
silent, and the first real test is during the incident. Seven concrete scenarios, grounded in source.

| # | Scenario (who / what / how) | Grounded in | Blast radius |
|---|---|---|---|
| **T-1** | **Portability cliff — the backup does not follow the new repo, and three manual steps have no failing signal.** `backup-db.yml` is gated `if: github.repository == 'menno420/superbot'` (:56), reads a **repo-scoped** secret `DATABASE_PUBLIC_URL` (:61), **and** its 400-day monthly tier is silently clamped to 90 days unless the repo's *Artifact and log retention* max is raised (`:131-136`). The new repo starts with **zero backup coverage** until someone re-ports the workflow, re-creates the secret, **and raises the retention setting** — **three** manual steps, none of which fails loudly if skipped. | `backup-db.yml:56,61,131-136`; prod-deploy §Backups one-time setup | The new **ledger-of-record** (money/audit spine) runs **unbacked** for an unknown window; a data-loss event during it has RPO = ∞. Silent because the failure mode is *nothing runs* — and a *skipped retention raise* silently caps history at 90 days. |
| **T-2** | **Schrödinger's backup — UNVERIFIED, never restore-tested.** The workflow self-labels `UNVERIFIED … Delete or disable this workflow if it proves unreliable` (:23-26). Its integrity check is `>=10 CREATE TABLE` (:119-124) — a **liveness** floor (the dump isn't empty), **not** a restorability proof. A subtly-broken dump (encoding, a truncated large table, a missing role/extension on the restore target) passes the 10-table floor and uploads as a "backup." | `backup-db.yml:23-26,119-124`; L-18 "self-labeled UNVERIFIED" | False confidence: the DR layer is unproven until a real restore is attempted, and by construction the **first real attempt is during an incident**. |
| **T-3** | **RPO undefined for the ledger-of-record — and *not* cheaply fixable.** Daily `pg_dump` ⇒ up to **~24 h** of writes unrecoverable on any restore-from-backup. No RPO number is stated. Worse, the tempting shortcut — "the append-only `audit_log` gives money/audit a near-continuous RPO for free" — is **false**: the `audit_log` sits **in the same Postgres the dump captures**, so on DB-loss it is lost with everything else. Append-only-ness buys a tight RPO *only if the log is durably shipped off-box at that cadence*, which nothing does today. | `backup-db.yml:31-32` (daily cron); `07` `audit_log` co-located; prod-deploy §Backups | On any restore, up to a day of **economy ledger + audit history** silently gone; "where did these coins come from?" is unanswerable for the lost window; and the fix is a *real* off-box-export or PITR build, not free. |
| **T-4** | **Rollback destroys the N-day window (the core gap).** Per §5.2 :1349-1351 / §5.4 the new bot writes only the **NEW** DB after cutover; the OLD DB is frozen; rollback re-deploys the old worker on that OLD DB. So **every write made through the new bot during window N lives only on the NEW DB** and vanishes the instant the old bot (authoritative again) resumes on the OLD DB. No reverse importer, no replay log, no declared-loss policy exists. | §5.2 :1349-1351; L-18 "rollback destroys all post-cutover writes"; FJ §4 #2 | The **safety lever itself** silently deletes N days of real user state — economy transactions, XP, tickets opened, mod actions, giveaways — across **every** production guild. *"A rollback lever whose data cost is unstated is not a safety lever."* |
| **T-5** | **Reverse-import is structurally impossible for collapsed / new-only writes.** The rebuild **collapses** schema (§5.1: session state → checkpoints; renamed/dropped tables; the whole point is to shed fragmentation). A write from a new-bot-only command, or into a collapsed checkpoint, has **no old-schema table to reverse into** — its forward importer mapping is *non-invertible*. Only stores whose forward mapping is a **non-collapsing bijection** (name-stable *or* pure-rename) can round-trip. Name-stability is guaranteed by §5.2 (:1335-1336) for only `{subsystem_bindings, economy_audit_log, ai_review_log, ai_answer_presets}`; XP/karma round-trippability rests on their *rename being invertible* (§2.4b), not on name-stability. | §5.1-5.2; §5.2 :1335-1336; design-spec decision 8; Q-0224 renames | Any disposition that *promises* full recovery is a lie by construction; the honest design **must** declare the un-round-trippable classes as loss — which forces the owner-gated call, not a silent default. |
| **T-6** | **The verify-restore job needs prod-like infra the CI lacks, and must never touch prod.** A verified-restore must restore into a real Postgres and boot the bot — the **same** Postgres-service-container gap already flagged for `golden-parity` (design-spec §6 linchpin: "this repo's own `code-quality` workflow runs no Postgres service container"). And the restore target's DSN **must** be forced `SB_DATA_PLANE=test` (vocab ⑥) so a verify-restore can **never** open or clobber prod. | design-spec §6 (linchpin); vocab ⑥ `assert_data_plane` | Without the plane rail, a mis-wired verify job could point a restored dump's DSN at prod; with it, structurally impossible (`RefuseBoot` before any network I/O). Infra cost is shared with `golden-parity`, not net-new. |
| **T-7** | **The verify-BOOT itself is a live side-effect hole (new).** "Boot the new bot to readiness 200" against a **~week-old restored prod snapshot** silently trips the frozen restart-safety pattern (vocab ⑤.3): **after `/ready` 200, boot-reconcile fires *every* overdue durable timer "exactly once" and the outbox relay flushes**. `SB_DATA_PLANE=test` contains **DB writes only** — it does **not** stop outbound Discord / scheduler side-effects. If the verify-boot uses a real gateway, a weekly reliability job emits **real announcements, giveaway draws, and scheduled fires into real guilds from stale restored data**. | vocab ⑤.3 (boot-reconcile fires post-ready); vocab ⑥ (plane = DB writes only) | A reliability job that is supposed to *prove* the backup instead *acts on the world* from a week-old snapshot — the exact "the safety machinery is itself the incident" anti-pattern (mirrors 11 T-6). |

**The through-line:** T-1/T-2/T-3 are the **backup layer's own** decay (portability incl. the retention
clamp, unproven, un-budgeted-and-not-free RPO) — a permanent, honestly-costed CI proof fixes them.
T-4/T-5 are the **rollback-data** gap — a declared, tiered, bounded disposition keyed on a *derived*
`rollback_class` fixes it, and T-5 is *why* it must be owner-gated. T-6/T-7 are the **safety envelope**
the proof machinery must satisfy (prod-like infra, plane-forced, **and side-effect-free at boot**). One
backbone answers all shapes.

---

## 2. DESIGN RESPONSE

One backbone: **the backup becomes a first-class ported artifact with a *continuous, side-effect-free*
verified-restore proof, an *honestly-costed* RPO, and a declared, bounded, tiered rollback-data
contract keyed on a mechanically-derived `rollback_class`.** Buildable depth on the port + CI proof +
the `rollback_class` derivation/fence; decision-ready depth on the three postures (§4).

### 2.1 Port the backup as a first-class new-repo artifact (de-repo-bind) — *decide-able by design*

The de-repo-bind is a **five-item** cutover checklist (the earlier draft named four and dropped the
retention-clamp step — T-1 / §8-4):

1. **Drop the repo-identity guard.** `if: github.repository == 'menno420/superbot'` (:56) becomes an
   input-driven guard (`vars.BACKUP_ENABLED`) or is removed — the new repo owns its own copy; the guard
   was a fork-safety relic, not a DR property.
2. **Re-create the secret as a named cutover step.** `DATABASE_PUBLIC_URL` is added to the new repo's
   Actions secrets — a line item in the **cutover runbook** (interlocks with FJ §4 #10 credential
   lifecycle; I *name* the one-time re-creation, the rotation contract is a separate cut, §6).
3. **Raise the repo's artifact-retention max to ≥400 days** (Settings → Actions → General → *Artifact and
   log retention*). Without it, `retention-days: 400` on the monthly tier is **silently clamped to 90**
   (`backup-db.yml:131-136`) — the long-retention tier the monthly cron exists for quietly evaporates.
   This is the **third silent manual step** T-1 names, and §2.2's proof now **checks it** (below).
4. **Graduate out of "UNVERIFIED."** The `delete if it proves unreliable` self-label (:23-26) is
   replaced by the continuous proof in §2.2 — the header's own precondition ("confirm … the dump is
   restorable") is finally *mechanized* rather than left to a human's one-time memory.
5. **Rename the integrity floor's comment** to state it proves **non-empty, not restorable** (:119-124)
   — a trivial honesty fix so no reader mistakes the liveness floor for a restore proof (the exact
   Q-0120 "a green that contradicts evidence" trap).

Keep the daily + monthly tiers, the failure-issue, and the PGDG-client install verbatim — they are
correct; only the repo-binding, the retention step, and the verification story change.

### 2.2 The continuous, side-effect-free verified-restore proof — CONSUMES dossier 11's definition (I add cadence + source + plane + a safe boot mode)

A new scheduled workflow `restore-verify.yml` (kernel-band CI, not a PR-required check — a
**reliability job**):

> download the **latest backup artifact** → restore into a **fresh Postgres service container**
> (shared infra with `golden-parity`, T-6) whose DSN is **forced `SB_DATA_PLANE=test`** (vocab ⑥
> `assert_data_plane` ⇒ structurally cannot be prod) → **boot the new bot in verify-boot mode to
> readiness 200** (below) → run the **dry-run invariant sweep** (dossier 11 §2.5) → **green iff boots
> AND sweep-clean.**

- **This is exactly dossier 11's "verified := boots + dry-run sweep clean"**, run *on a schedule against
  the real artifact* instead of once, by hand, at setup. I **consume** the definition; I own only the
  **cadence** (weekly ≥ backup cadence), the **artifact source** (the latest daily dump), the
  **plane-forced target** (⑥), and — new — the **side-effect-free boot mode**. No new definition of "verified."
- **The verify-boot mode — the T-7 fix (buildable, not owner-gated: contained, reversible, plane-fenced).**
  A new operational config flag **`SB_VERIFY_BOOT: BOOL` (default `False`; a `ConfigSpec`, vocab ⑥ — an
  additive 48th operational field, §8-5)** puts the composition root into a boot profile that is
  **side-effect-free by construction**:
  - **(a) Fake-HTTP transport, no real gateway/token.** discord.py is driven by the **golden-parity
    fake-HTTP-over-the-real-state-machine harness** (`parity/`, design-spec :1431-1435) — the *same*
    mechanism `golden-parity` already uses. There is **no gateway connect and no bot token**, so any
    outbound send/announce/draw hits the fake sink, never a real guild. (`assert_intents`/gateway-connect
    is skipped for `SB_VERIFY_BOOT`, exactly as the harness already does.)
  - **(b) Boot-reconcile fires + outbox relay SUPPRESSED.** The scheduler's `PollSupervisor` fire loop /
    boot-reconcile (vocab ⑤.3) and the outbox delivery relay (`08`) are **not started** under
    `SB_VERIFY_BOOT`. Reaching `/ready` 200 is a *readiness* fact (preflight → compiler boot_gate → DB init
    → RUNNING); **boot-reconcile is a post-ready steady-state step (⑤.3), so suppressing it does not weaken
    the "boots to 200" proof** — it only stops the stale snapshot's overdue timers from ever firing.
  - **(c) Plane-fenced.** `SB_DATA_PLANE=test` is still asserted (⑥) — even the DB-write path is
    structurally test-only. `SB_VERIFY_BOOT=True` **requires** `SB_DATA_PLANE=test` (a preflight
    invariant: verify-boot on a non-test plane ⇒ `RefuseBoot`), so the two rails compose.

  The **"verified" contract is therefore `verified := boots to /ready 200 under SB_VERIFY_BOOT (fake-HTTP,
  reconcile+relay suppressed, test-plane) AND the dry-run sweep is clean`** — no real side-effect can
  escape a verify run.
- **Privacy / retention of the weekly prod-data copy (closes the new #11 copy-site).** `restore-verify.yml`
  is a **new recurring instance of FJ §4 #11 "ungoverned prod-data copies in the proving pipeline"** — it
  pulls the latest prod `pg_dump` (member PII + any secrets stored in `settings`) into an Actions runner
  weekly. Its posture is stated, not left open:
  - The restored snapshot lives **only** in the job's **ephemeral runner + Postgres service container**,
    which GitHub destroys at job end. The job **uploads no artifact of the restored data** — only the
    pass/fail + the counts metric (`last_verified_restore_age`, `rows_read`). No restored-DB dump ever
    leaves the runner.
  - `permissions:` is minimal — `contents: read` + `issues: write` (failure issue only); no third-party
    action gets DB access; the dump is fetched with the workflow's own token from the same-repo artifact.
  - The **source dump's** own retention/erasure lifecycle (how long the daily/monthly artifacts live, PII
    minimization in the dump) is a **privacy cut, not backup/DR** — deferred with a labeled bound and a
    pointer to **rubric class 12** (privacy/retention/erasure), the same home sibling 11 §6 uses (§6 here).
- **Fixes T-1 + T-2 together, and checks the retention step:** a job that restores the *new-repo* artifact
  weekly *is* the proof the backup both exists and works — the failure mode flips from silent-absence to a
  red CI job + a failure-issue (reusing the workflow's existing issue-on-failure pattern). The job
  **additionally asserts the latest MONTHLY artifact exists and is not clamped** (its `retention-days` came
  back as 400, not 90), turning §2.1 step 3 from an un-checked manual step into a red signal if skipped.
- **The `last_verified_restore_age` metric** it emits is the backup-health signal §2.5 puts on the
  scoreboard and §2.3 reads as the RPO witness.

### 2.3 The RPO contract — a stated number + a tiered source, *honestly costed* (fixes T-3)

State an explicit RPO, tiered by store value-class. **Correction over the earlier draft:** under the
**current built posture (daily `pg_dump` + monthly tier, no off-box streaming)** *every* store — money/
audit included — has RPO **≤ 24 h**, because the append-only `audit_log` is **co-located in the very
Postgres the dump captures**; on DB-loss it dies with everything else. Append-only-ness buys a tight RPO
**only if a continuous off-box source exists** — and building one is a real cost, not free.

| Tier | Store class (keyed on 09's `StoreSpec.bears_value` / `invariant_tag` INV-F/G/K) | RPO under the CURRENT posture (`pg_dump` only) | RPO reachable — and the *real* cost |
|---|---|---|---|
| **Ledger/audit** | `bears_value=True` — `economy_audit_log`, XP, karma, treasury, the `audit_log` spine | **≤ 24 h** — the `audit_log` is append-only but **in the dumped Postgres**, so DB-loss loses it too; append-only-ness is *not* off-box durability | **minutes**, but **not free**: either **(B)** a continuous **off-box export of the `audit_log`** (WAL/logical-replication stream, or an append-only ship-to-object-store of `audit_log` rows), scoped to the `bears_value` spine — a real build; **or (C)** Railway PITR (whole-DB) |
| **Everything else** | non-value stores, checkpoints, presets, bindings | **≤ 24 h** (the daily `pg_dump` floor) | minutes **only** under **(C)** whole-DB PITR; not independently worth an off-box stream |
| **(optional)** | whole-DB point-in-time | — | **(C)** Railway PITR (Pro-plan-gated; already flagged railway-setup-plan §6 R2) ⇒ **≈ minutes**, whole-DB, if the plan is upgraded |

**The corrected insight:** the append-only `audit_log` makes the money/audit spine the **cheapest store
to give a tight RPO *once a continuous off-box sink exists*** — you can ship a compact append-only stream
instead of the whole DB — **but under `pg_dump`-only it is neither free nor tighter than 24 h.** The RPO
**number**, and whether to *build* the off-box audit-log export (B) or *buy* Railway PITR (C), is the
owner call (§4 Q1). *(This tiering depends on 09's `bears_value`; if that field is renamed/rejected at
Gate-0, the tier key re-binds — §8-1.)*

### 2.4 The rollback-data disposition — a declared, bounded, tiered contract keyed on a *derived* `rollback_class` (fixes T-4/T-5)

The core mechanic. Four moves.

**(a) The window's ledger writes are *forensically* captured — but the audit_log is NOT a complete money
replay log; reverse-import does not rely on it being one.** Every post-cutover auditable mutation the new
bot makes is an append-only row in the `audit_log` spine (`07`) + `event_outbox` (`08`), keyed by
`mutation_id`, with `prev_value`/`new_value`/`occurred_at`. **But two facts bound what that buys us:**

- **Completeness dependency on 11 T-2 (stated, not assumed).** Sibling 11 **T-2** documents that
  *value-bearing aggregate writes bypass the audited seam* in the **legacy** bot (`set_coins`/`add_coins`,
  `economy.py:200-215`, emit **no** ledger/audit row) — and that INV-F is a *compile-time* fence only, not
  an at-rest guarantee. So an `audit_log`-only replay has a **completeness hole exactly where money can
  move un-audited.** In the **new** bot this hole is closed *by construction*: the vocab **§③.4
  `audit_completeness` fence** requires every `effect="mutating"` ref to route through the audited K7 seam,
  so post-cutover new-bot money moves *do* mint a row. This dossier's reverse-import **depends on** that
  fence for the LEDGER tier and **cites 11 T-2** for why it cannot lean on `audit_log` completeness for
  historical/aggregate value.
- **Aggregate reverse-import does not read the log at all (so audit gaps can't strand money).** For
  AGGREGATE stores the reverse-importer copies the **absolute aggregate value**, not a log replay (below,
  (c)) — so value that moved *even without* an audit row is still captured. The `audit_log` is therefore
  the **forensic + `REPLAY_INTENT` substrate and the whole-window total**, *not* the value-completeness
  guarantee. The "replay log the concern asks for" exists **for forensics**; the *value* guarantee is the
  per-store delta (ledger by `mutation_id` + aggregate by absolute value), robust to any audit gap.

The delta boundary is **`cutover_flip_ts`** (defined below), and the design question is what to *do* with
each store's post-`cutover_flip_ts` delta on rollback.

**`cutover_flip_ts` — the delta boundary (was the undefined `cutover_freeze_ts`; renamed + pinned).** The
earlier draft used `cutover_freeze_ts` without defining it, and *freeze* is the **wrong** instant. Per
§5.4 step (4) the sequence is **`freeze old bot → final import delta (OLD→NEW) → flip Railway`**: between
freeze and flip the old bot is frozen (writing nothing) and the forward importer carries the last OLD rows
into the NEW DB (those rows keep their original `occurred_at`, all `< freeze`). **The new bot's own writes
begin at the *flip*.** So the reverse-import boundary is the **flip instant**, and reading NEW-DB
`audit_log WHERE occurred_at >= cutover_flip_ts` selects **exactly** the new-bot-authored rows with **no
overlap** with the already-imported historical delta (which is all `< freeze <= cutover_flip_ts`).

- **Definition:** `cutover_flip_ts` = the UTC instant the Railway service flips the new worker live
  (§5.4 step 4 end).
- **Persistence + writer:** a **global kernel marker** — a `settings_keys` constant `CUTOVER_FLIP_TS`
  (global scope, `guild_id=None`), written **once** by the cutover-runbook *flip* operation through the
  audited settings seam (never `os.getenv`), read by the reverse-importer and the scoreboard. (A one-row
  `sb_cutover_marker(flip_ts timestamptz)` fresh-chain table is the equivalent home if a settings key is
  undesirable; either way it is one authoritative instant.)
- **Precision:** `timestamptz`, second precision, monotonic vs the new bot's first write (the flip
  precedes the new bot accepting any command, so no new-bot row can predate it).

**(b) `StoreSpec.rollback_class` is DERIVED, not a hand-set REQUIRED field — a mechanical classification
of round-trip disposition.** The earlier draft made `rollback_class` a REQUIRED field with no default and
no rule, so every store was a fresh manual guess and the enum's "round-trippable" criterion fought the
Q3 posture (which reverse-imports only money). The fix: **the manifest compiler *derives* `rollback_class`
from two grounded inputs, so it is mechanical and consistent**:

```python
class RollbackClass(StrEnum):
    REVERSE_IMPORTABLE = "reverse_importable"  # forward mapping is a non-collapsing bijection AND bears_value → reverse-imported
    DECLARED_LOSS      = "declared_loss"       # non-invertible forward mapping, OR invertible-but-not-value-bearing → loss is DECLARED + signed
    REPLAY_INTENT      = "replay_intent"       # OWNER-set narrowing override on a REVERSE_IMPORTABLE store whose auto-replay is unsafe (later band, §6)

# on 09's version-extended StoreSpec (sb/spec/versioning.py — a sibling of bears_value/version_policy, NOT the base §2.8 StoreSpec):
    rollback_class: RollbackClass              # [DERIVED] computed by the compiler; NOT hand-set (except the REPLAY_INTENT override)
```

**Input 1 — forward-mapping invertibility (`forward_map_kind`), read off the importer's alias map (§5.2).**
The forward importer already knows, per store, how it maps OLD→NEW (it must, to move rows — §5.2 "the
manifest's generated alias maps and store specs"). Its `forward_map_kind` is grounded in existing signals,
not a new judgment:

| `forward_map_kind` | Grounded in | Invertible (non-collapsing bijection)? |
|---|---|---|
| `NAME_STABLE` | the §5.2 :1335-1336 name-stable set (`subsystem_bindings`, `economy_audit_log`, `ai_review_log`, `ai_answer_presets`) | **Yes** |
| `RENAME` | an alias-map entry that is a **pure column/table rename** (a bijection — e.g. an invertible Q-0224 XP/karma rename) | **Yes** |
| `COLLAPSE` | `checkpoint_class == session` (session state → checkpoints, §5.1) or an alias-map entry that **merges/aggregates** many old rows into one new row | **No** |
| `NEW_ONLY` | no old-schema source table (a new-bot-only feature) | **No** |
| `DROP` | a `store_retirements.yml` entry (SF-g `disposition`, vocab §⑧) | **No** |

**Input 2 — `bears_value`** (09's field): does the store hold money/audit-bearing value?

**The derivation table (mechanical — a builder computes, never guesses):**

| `forward_map_kind` invertible? | `bears_value` | `checkpoint_class` | → `rollback_class` | Why |
|---|---|---|---|---|
| **No** (`COLLAPSE`/`NEW_ONLY`/`DROP`) | any | any | `DECLARED_LOSS` | structurally cannot round-trip (T-5) |
| **Yes** (`NAME_STABLE`/`RENAME`) | `True` | `ledger`/`aggregate` | `REVERSE_IMPORTABLE` | invertible **and** money/audit — the one class where loss is unacceptable; the reverse-importer runs (Q3 posture B) |
| **Yes** | `False` | any | `DECLARED_LOSS` | round-trippable **but** its loss is acceptable (re-derivable config/bindings/presets); Q3 posture B reverse-imports **only** money, so it is declared-loss by *posture*, not by *capability* |
| **Yes** | `True` | (owner override) | `REPLAY_INTENT` | a value-bearing REVERSE_IMPORTABLE store whose auto-replay the owner judges unsafe (command surface changed) → human-reviewed list; the **only** hand-set value, and it only ever *narrows* an otherwise-REVERSE_IMPORTABLE store (§6) |

- **Corrected criterion (vs the earlier draft's "name-stable"):** `REVERSE_IMPORTABLE` ⟺ *the forward
  mapping is invertible (non-collapsing bijection) **and** the store is value-bearing* — **not** merely
  "name-stable." This is what grounds XP/karma's inclusion: they are `REVERSE_IMPORTABLE` **iff** their
  Q-0224 rename is a pure bijection (`forward_map_kind == RENAME`), and become `DECLARED_LOSS` the moment a
  rename *collapses/merges* them. `economy_audit_log` is grounded on §5.2 name-stability; XP/karma on
  rename-invertibility (§8-4, correcting SI-4).
- **Relationship to `checkpoint_class`:** `checkpoint_class == session` is the **collapse short-circuit**
  (⇒ non-invertible ⇒ `DECLARED_LOSS`) — the same enum 09/§2.8 already encode. `rollback_class` is **not**
  derivable from `checkpoint_class` *alone* (a `ledger`/`aggregate` store can still be `DECLARED_LOSS` if
  its rename collapses or it is new-only), which is why the derivation reads `forward_map_kind` **and**
  `bears_value` on top of it. It lives on **09's version-extended `StoreSpec`** (beside `bears_value`),
  because it *reads* `bears_value` — never on the base §2.8 six.

**(c) Reverse-importer semantics per tier (buildable — the `tools/importer/reverse/` builder needs no
further decision).**

| `rollback_class` | What the reverse-importer does on rollback | Idempotency |
|---|---|---|
| `REVERSE_IMPORTABLE`, **LEDGER** rows (**`economy_audit_log` only** — the one `NAME_STABLE`, OLD-schema-resident economy ledger, §5.2 :1335-1336. **NOT** the new-bot `audit_log` spine: it has no OLD-schema home ⇒ `forward_map_kind == NEW_ONLY` ⇒ `DECLARED_LOSS` by the §2.4b derivation, and its post-flip window slice is the forensic + `REPLAY_INTENT` substrate only — it never round-trips into the OLD DB, §2.4a) | **re-insert each post-`cutover_flip_ts` row into the OLD DB by its `mutation_id`** (`INSERT … ON CONFLICT (mutation_id) DO NOTHING`) — never a per-mutation *replay of effects* | **idempotent** by `mutation_id` PK (`once()`-guarded, `07` :409); a re-run re-inserts nothing |
| `REVERSE_IMPORTABLE`, **AGGREGATE** rows (e.g. `xp.coins`) | **copy the NEW *absolute* aggregate value over the frozen OLD value via upsert-by-natural-key** (`(user_id, guild_id)`) — **never** replay per-mutation aggregate deltas (which would double-apply under upsert and is not a "delta" for a value with no per-row key) | **idempotent** — writing the same absolute value twice is a no-op; robust to any `audit_log` gap (it reads the aggregate, not the log) |
| `DECLARED_LOSS` | not reverse-imported — enters the loss manifest (below) | n/a |
| `REPLAY_INTENT` | the `audit_log` slice becomes a **human-reviewed** replay list — **never** auto-replayed | n/a |

The reverse-importer is the **§5.2 forward importer's mirror** (`tools/importer/reverse/`), reusing its
upsert-by-natural-key + machine-readable stop-codes, bounded to the `REVERSE_IMPORTABLE` set only.

**The `DECLARED_LOSS` loss-manifest — two artifacts (row-counts *and* a per-subject breakdown).** The
earlier draft said "row counts by store … users are notified" — but per-user notification/compensation
needs a **per-subject affected-amount** breakdown, not aggregate counts. Both are produced from the same
per-store post-`cutover_flip_ts` delta:

- **M1 — the owner sign-off summary** (the signed artifact): one row per `DECLARED_LOSS` store —
  `{store, rollback_class, forward_map_kind, rows_lost, guilds_affected}`. This is what the owner reviews
  and signs (SF-g signed-disposition pattern).
- **M2 — the per-subject compensation ledger** (feeds the FJ §4 #9 comms/ring hook): rows
  `{guild_id, user_id, store, value_lost}`, derived from each **value-bearing** `DECLARED_LOSS` store's
  post-flip delta keyed by `(guild_id, user_id)`. A non-value collapsed store (no per-user amount)
  contributes **no** M2 rows — only an M1 count and a "this feature's state reset" notification. M2 is the
  granularity the notification/compensation actually needs; I **FEED** the comms plan the M2 shape, I do
  not own it.

**(d) Make N small and the posture forward-fix-first, so `DECLARED_LOSS` is cheap by construction.** The
default response to a post-cutover bug is a **hotfix forward**, not a rollback; rollback is the last
resort. Combined with the **progressive-exposure ring** (FJ §6 T3: volunteer guilds before the full swap)
and a **short N**, the number of guilds × days at risk — and thus the `DECLARED_LOSS` blast radius — is
bounded *before* the disposition fires. The **value of N** is the owner carry (Stage-3, Tier-3 line 359);
the **mechanism** is designed here.

**The rollback playbook (a written CUT-3 artifact):** rollback decision → freeze new bot → export each
store's `audit_log`/aggregate delta since `cutover_flip_ts`, **bucketed by the store's derived
`rollback_class`** → reverse-import the `REVERSE_IMPORTABLE` tier into the OLD DB (audited, idempotent —
ledger by `mutation_id`, aggregate by absolute-value upsert; reuses the §5.2 importer's discipline +
stop-codes) → emit the `DECLARED_LOSS` **M1 + M2** manifest for owner sign-off → re-deploy old worker →
notify guild admins (M2-driven per-user, M1-driven per-store). The playbook lands beside the §5.4
migration shape.

### 2.5 The fence + the scoreboard hooks (so it cannot evaporate — V-3)

- **`rollback_class_resolved` compile fence** (`manifest-validate`, §6 required check #2, beside
  `leaderboard-has-writer`): every `StoreSpec` **MUST resolve** to a `rollback_class` — i.e. it declares a
  `forward_map_kind` (or one is derivable from `checkpoint_class == session` / `store_retirements.yml` /
  absence-of-source) **and** `bears_value` is set — else `SEMANTIC_VIOLATION ("rollback_class_unresolved")`
  → CI-red. **And the reverse-importer's covered set MUST equal exactly the `REVERSE_IMPORTABLE` set** —
  a REVERSE_IMPORTABLE store the reverse-importer doesn't cover, or a covered store that isn't
  REVERSE_IMPORTABLE, is `SEMANTIC_VIOLATION ("reverse_importer_coverage_gap")`. *This is the structural
  fix for T-4: you cannot ship a store whose rollback-data disposition is unresolved, nor a reverse-import
  set that silently drifts from the derived classification.* Same one-way-door as SF-g's signed `disposition`.
- **Two new §5.4 shadow-scoreboard lines**, so "the data cost of rolling back *right now*" is a
  **read-off, not a feeling** (the §5.4 posture, extended from cutover-exit to rollback-cost):
  - `rollback_window_writes_by_class` — **computed per-store, not from the generic `audit_log`.** *Correction:*
    the `audit_log` DDL (`07` :408-422) carries `subsystem/mutation_type/target/scope` but **no `table`/`store`
    column**, so it cannot be partitioned by `rollback_class` (which is per-store). The line is therefore
    computed by walking **each store's** post-`cutover_flip_ts` delta and bucketing by that store's derived
    `rollback_class`: LEDGER stores count appended rows `WHERE occurred_at >= cutover_flip_ts`; AGGREGATE
    stores count **distinct natural keys** with a post-flip change (via the store's companion ledger's
    post-flip keys, or an `updated_at >= cutover_flip_ts`); `DECLARED_LOSS` stores count the same way. The
    generic `audit_log` supplies a **whole-window total** (a cross-check) and the `REPLAY_INTENT` forensic
    list — it is **not** the per-class partition substrate.
  - `last_verified_restore_age` — the §2.2 backup-health / RPO witness (a stale value = the backup proof
    is failing = do not cut over).
- **The verified-restore CUT gate** — consumes dossier 11's definition **and cross-references 11 §4 Q2**
  rather than re-deciding it (§4 Q2 here). Cutover cannot proceed unless the most recent
  `restore-verify.yml` run is green (the backup-restorability + freshness precondition — 13's genuine add,
  recommended HARD). The **invariant-correctness granularity within the sweep** (which invariants
  hard-block) is decided **once**, in **11 §4 Q2** — this dossier does not fork it.

---

## 3. LANDING SITE (so it cannot evaporate — V-3)

| Response | Lands as | Concrete home |
|---|---|---|
| Port + de-repo-bind the backup, incl. the 400-day retention step (§2.1) | **Ops/CI artifact in the new repo** + a **five-item** cutover-runbook step | new-repo `.github/workflows/backup-db.yml` (guard dropped); cutover runbook (secret re-creation + repo retention-max raise) |
| `restore-verify.yml` continuous, side-effect-free proof (§2.2) | **A scheduled reliability CI job** (Postgres-service container, plane-forced, `SB_VERIFY_BOOT` boot mode) — *not* a PR-required check | new-repo `.github/workflows/restore-verify.yml`; consumes dossier 11 §2.5 sweep + shares `golden-parity`'s Postgres-service infra + fake-HTTP harness (design-spec §6 / :1431-1435) |
| `SB_VERIFY_BOOT` side-effect-free boot profile (§2.2) | **A new operational `ConfigSpec`** (vocab ⑥, additive 48th field) + a composition-root boot profile (fake-HTTP transport, reconcile+relay suppressed, `SB_DATA_PLANE=test` required) | `sb/spec/config.py` `CONFIG_FIELDS`; composition-root boot leg |
| RPO contract + honestly-costed tiered source (§2.3) | **A stated RPO in the design spec** + Stage-3 consolidation line | design-spec §5 (RPO number); the ledger tier's tight-RPO *option* is off-box-export (B) or PITR (C), not the in-DB `audit_log` |
| `RollbackClass` enum + **DERIVED** `rollback_class` on 09's version-extended `StoreSpec` (§2.4b) | **A compiler-derived Gate-0 grammar facet** on **09's `sb/spec/versioning.py` `StoreSpec`** (sibling to `bears_value`/`version_policy`), **NOT** the base §2.8 six | `sb/spec/versioning.py` (09's StoreSpec); derivation in the manifest compiler; SubsystemManifest export |
| `cutover_flip_ts` marker (§2.4a) | **A global kernel marker** written once by the cutover-runbook flip op | `settings_keys.CUTOVER_FLIP_TS` (global) via the audited settings seam, **or** a one-row `sb_cutover_marker` fresh-chain table |
| `rollback_class_resolved` + reverse-importer-coverage fence (§2.5) | **`manifest-validate` CI gate** (§6 required check #2), beside `leaderboard-has-writer` | manifest compiler fence |
| Narrow reverse importer for the REVERSE_IMPORTABLE tier (§2.4c) | **The §5.2 importer's mirror** (`tools/importer/reverse/`) — ledger by `mutation_id`, aggregate by absolute-value upsert; golden-tested against a snapshot fixture | design-spec §5.2 (importer family); the rollback playbook |
| Loss-manifest **M1 + M2** (§2.4c) | **A signed CUT-3 artifact (M1)** + a **per-subject compensation ledger (M2)** feeding the comms hook | rollback playbook; FJ §4 #9 comms/ring plan (fed, not owned) |
| Rollback playbook (§2.4d) | **A written CUT-3 artifact** beside the §5.4 migration shape | design-spec §5.4; CUT-3 gate list |
| Verified-restore CUT gate + 2 scoreboard lines (§2.5) | **CUT-3 gate** (backup-restorability precondition HARD; sweep granularity = 11 §4 Q2) + **§5.4 compat-scoreboard** lines | design-spec §5.4 (scoreboard); Stage-3/CUT-3 gate list |
| Weekly prod-data copy privacy posture (§2.2) | **Named in the privacy/retention cross-cut** (runner-ephemeral, no restored-data artifact, minimal perms); source-dump lifecycle deferred | rubric class 12 (privacy/retention/erasure — dossier fed, not owned) |
| The whole DR posture as a reliability lens | **Rubric class 13** (reliability/security non-functional — dossier 10) — DR is a class-13 probe | rubric §8 (owned by dossier 10; I *feed* it) |

---

## 4. OWNER-GATED

| # | Decision | Options | Recommendation | Gate |
|---|---|---|---|---|
| 🔒 **Q1** | **RPO target + source tier (honestly costed).** *(the concern's "RPO the backup must meet")* | **(A)** daily `pg_dump` only — flat RPO **≤ 24 h for *all* stores, money/audit included** (the append-only `audit_log` gives *nothing* tighter, being co-located in the dumped DB) · **(B)** `pg_dump` floor **+ build a continuous off-box `audit_log` export** (WAL/logical-replication or append-only ship-to-object-store) scoped to the `bears_value` spine ⇒ minutes-RPO reconstructable money/audit — **a real build, not free** · **(C)** Railway PITR (RPO ≈ minutes, whole-DB) — requires a plan upgrade | **(A) is the honest built floor today.** Reaching minutes-RPO for the money spine is the genuine owner call between **(C)** buying PITR (least code, whole-DB) and **(B)** building the off-box audit-log export (more code, scoped to money, no plan cost). Recommend **(C) if the plan upgrade is acceptable**, else **(B)**. **Do not** present near-continuous money RPO as "free" — the earlier draft's error (§8-3). **A genuine owner call — plan-cost vs build-cost vs 24 h-acceptable — options+recommendation only.** | owner call (plan cost / build cost) |
| 🔒 **Q2** | **Verified-restore as a HARD CUT-3 gate vs advisory — *deferring the invariant-granularity half to 11 §4 Q2*.** *(the concern's "verified-restore a HARD CUT-3 gate?")* | Two *separable* legs: **(i) backup-restorability precondition** — the latest `restore-verify.yml` is green (boots + fresh): **(A)** HARD · **(B)** advisory (`last_verified_restore_age` line only). **(ii) invariant-correctness granularity** — which invariants inside the sweep hard-block: **decided ONCE in 11 §4 Q2** (11 recommends: HARD on `bears_value` `RECONCILIATION`+`TERMINAL_ONCE`, advisory on the rest, owner-signed quarantine override) | **Leg (i): (A) HARD** — a backup you have never proven restorable is not a backup (T-2), and because §2.2 makes the proof *continuous*, the gate is almost always already green, so HARD rarely *blocks* — it only catches "the backup silently broke" at the one moment it matters. **Leg (ii): defer to 11 §4 Q2 — do not fork it here.** The earlier draft's "plain HARD (A)" recommendation **diverged** from 11's finer (C); this dossier now cross-references 11 and recommends *only* the backup-restorability precondition, leaving the sweep granularity to 11 (§8 / SI-2). | owner posture (leg i) + **11 §4 Q2** (leg ii) |
| 🔒 **Q3** | **Rollback-data disposition + window N.** *(the concern's core owner call — "reverse-import / replay-log / declared-loss + window N")* | **(A)** pure `DECLARED_LOSS` + short N + owner sign-off (cheapest; loses the window's money rows too) · **(B)** `DECLARED_LOSS` **+ a narrow reverse-import valve for the derived `REVERSE_IMPORTABLE` (invertible-∧-value-bearing) tier** + short forward-fix-biased N + owner-signed **M1/M2** loss manifest · **(C)** full reverse-import of everything — **rejected**: structurally impossible for collapsed / new-only stores (T-5) | **(B).** Full recovery is a lie by construction (T-5), so the honest design is: **round-trip the one class where loss is unacceptable (invertible-∧-value-bearing money/audit — ledger by `mutation_id`, aggregate by absolute-value copy), declare the rest lost, keep N short and forward-fix-first so the declared loss is small.** The **value of N** stays the owner carry (Stage-3, Tier-3 line 359). **A genuine owner-only call** — a data-loss policy with a real reverse-importer build cost; near-irreversible either way. **Options+recommendation only.** | owner call (data-loss policy + N) |
| ▹ **Q4** | **De-repo-bind mechanics + retention step + the integrity-floor comment fix (§2.1).** | **(A)** drop the `github.repository` guard, re-create the secret, **raise the repo artifact-retention max to ≥400**, rename the `>=10 CREATE TABLE` comment to "non-empty, not restorable" · **(B)** keep the guard parameterized on a repo var | **(A)** — contained, reversible, test-covered by §2.2's continuous proof (which now *checks* the retention step). **Decide-able by design; flagged.** | design default |

---

## 5. RETIREMENT MAP

| Row (FJ §2 L / §4 gap / §6 owner-queue) | How this dossier retires it | Status |
|---|---|---|
| **L-18 — backup/DR doesn't survive cutover; no verified-restore gate; rollback destroys post-cutover writes** | **All three legs.** Backup-survives-cutover: **CLOSED** (§2.1 five-item port + de-repo-bind). Verified-restore gate: **CLOSED, co-owned with 11** — 11 defined "verified" (**PARTIAL on its own**, its §5), and this dossier *completes* it (§2.2 continuous, **side-effect-free** CI proof + §2.5 CUT-3 gate). The **combined** verified-restore leg is CLOSED; 11's "PARTIALLY CLOSED" is scoped to 11's *own* contribution, not the combined leg — **no contradiction** (SI-2). Rollback-data disposition: **CLOSED** (§2.4 declared tiered contract + *derived* `rollback_class` fence + reverse-import valve + M1/M2 manifest + playbook). | **CLAIMED / CLOSED** (verified-restore leg **co-owned with 11**) |
| **FJ §4 #2 — "Rollback destroys post-cutover data / backup-DR doesn't survive cutover"** (the ★ completeness gap = L-18) | Same as L-18; this is its §4 entry. | **CLAIMED / CLOSED** |
| **FJ §6 owner-queue T2 addition — "Rollback-data disposition: reverse-import / replay log / declared-loss sign-off?"** (line 365, stress-D-3 + critics) | Exactly §2.4 (the derived-`rollback_class` tiered contract) + **Q3** (the owner call with options+recommendation). | **CLAIMED** (mechanism designed; the posture is Q3) |
| **FJ §6 Tier-3 carry — "CUT-3 rollback window N set at Stage 3"** (line 359) | The **mechanism** that gives N meaning is designed (§2.4d — N governs the `DECLARED_LOSS` blast radius, read off `rollback_window_writes_by_class`); the **value of N** stays the owner's Stage-3 carry. | **PARTIALLY CLOSED** (mechanism closed; N-value = owner) |
| **RPO target** (implied by L-18; the concern's second owner question) | §2.3 states an explicit tiered RPO **and corrects the "free near-continuous money RPO" error**; **Q1** is the owner call on the number + build-vs-buy for minutes-RPO. | **CLAIMED** (contract stated honestly; number + source = Q1) |
| **FJ §4 #9 — no user-facing change-communication mechanic** | The `DECLARED_LOSS` **M2 per-subject compensation ledger → guild-admin notification** interlocks with the comms/ring plan; I **FEED** the M2 shape (the notification trigger), do not own the comms plan. | **FEEDS (not owned)** |
| **FJ §4 #10 — credential lifecycle** (the `DATABASE_PUBLIC_URL` secret) | I **name** the one-time secret **re-creation** as a cutover-runbook step (§2.1); the rotation/revocation/compromise contract is a separate credential cut. | **ADJACENT (re-creation named; rotation deferred, §6)** |
| **FJ §4 #11 — ungoverned prod-data copies / retention in the proving pipeline** | `restore-verify.yml` is a **new weekly copy site**; §2.2 states its runner-ephemeral / no-restored-artifact / minimal-perms posture, and defers the source-dump *retention lifecycle* to rubric class 12 (matching 11 §6). | **NAMED + posture stated; retention lifecycle deferred (§6, rubric 12)** |
| **Rubric class 13 (reliability/security non-functional) — FJ §8 / dossier 10** | The DR posture (backup-health, verified-restore, rollback-cost read-off) is a **class-13 probe surface**; I feed it, dossier 10 owns the rubric edit. | **FEEDS (not owned)** |

---

## 6. DEFERRALS (labeled)

| Deferral | Reason | Bound |
|---|---|---|
| **The value of window N** | Owner-gated data-loss policy (Q3); a Stage-3 / CUT-3 carry (FJ Tier-3 line 359). | The mechanism (§2.4d) is designed and reads N off `rollback_window_writes_by_class`; only the number is deferred. |
| **`REPLAY_INTENT` — automated command-level replay** | The command surface **changed** (Q-0224 renames, D-5 drops), so auto-replaying a window's mutations as commands is unsafe. | v1 = a **human-reviewed** replay list from the `audit_log` slice; `REPLAY_INTENT` is the owner's *narrowing* override on a REVERSE_IMPORTABLE store (§2.4b), reserved so the later band slots in with zero grammar change. |
| **Full reverse-import of collapsed / new-only stores** | **Structurally impossible** (T-5) — the rebuild sheds schema; these rows have no old-schema home (non-invertible `forward_map_kind`). | Not a build deferral — a declared reality: `DECLARED_LOSS` is the *honest* disposition, signed by the owner (M1/M2), bounded by a short N. |
| **Minutes-RPO source** (off-box `audit_log` export **(B)** or Railway PITR **(C)**) | **Owner cost decision** — a real build (B) or a plan upgrade (C); railway-setup-plan §6 R2 records the PITR gate. | Q1; the `pg_dump` daily+monthly tiers stand alone at ≤ 24 h without either. |
| **Retention / erasure lifecycle of the weekly restored snapshot + source dumps** (FJ §4 #11) | Scope — a **privacy/retention** concern (rubric class 12), not backup/DR. §2.2 already fixes the *copy-site* posture (runner-ephemeral, no restored-data artifact, minimal perms); the *lifetime/PII-minimization* of the source dumps is the privacy cut. | Pointer to rubric class 12 (same home 11 §6 uses); the verify gate is the hook it plugs into. |
| **Credential rotation / revocation / compromise-recovery** for `DATABASE_PUBLIC_URL` / token / DSN (FJ §4 #10) | Scope — a **credential-lifecycle** cut, not backup/DR. | I name the one-time re-creation; the lifecycle contract is a separate cross-cut. |

All deferrals sit behind a designed seam; none blocks porting the backup, building the continuous
side-effect-free verified-restore proof, adding the derived-`rollback_class` fence, or writing the
rollback playbook now.

---

## 7. Architecture rules honored (cited)

- **All DB access via `utils.db.*` / `sb/kernel/db/*` (asyncpg only)** — the reverse importer and the
  restore-verify boot read/write only through the db seam; the restore target is a *separate* Postgres,
  never a raw `pool.execute` against prod. The verify job's DSN is **forced `SB_DATA_PLANE=test`**
  (vocab ⑥ `assert_data_plane`), and `SB_VERIFY_BOOT=True` **requires** the test plane, so it structurally
  cannot open prod.
- **All auditable mutations through the audited seam** — the reverse importer's writes into the OLD DB
  follow the §5.2 importer discipline (upsert-by-natural-key, stop-codes, owner-reviewed dry-run); the
  LEDGER tier re-inserts by `mutation_id`, the AGGREGATE tier upserts the absolute value — both idempotent,
  both forensic. The `cutover_flip_ts` marker is written through the audited settings seam, never
  `os.getenv`. No disposition mutates state silently.
- **`services` must NOT import `views`; cogs never import cogs** — none of this touches cog/view code; it
  is CI workflows (`backup-db.yml`, `restore-verify.yml`), the `tools/importer/reverse/` family, a
  compiler-derived `StoreSpec` facet, a manifest fence, and a `ConfigSpec` — all outside the runtime layer
  table. The `SB_VERIFY_BOOT` boot profile drives discord.py via the golden-parity fake-HTTP harness
  (`parity/`), a test seam, never a real gateway.
- **`settings_keys` constants / `ConfigSpec`, never raw env** — the backup DSN, the RPO cadence, `N`, and
  `CUTOVER_FLIP_TS` are config/spec/settings fields (`DATABASE_PUBLIC_URL` a repo secret, `SB_VERIFY_BOOT`
  a `ConfigSpec`, `rollback_class` a derived StoreSpec facet, `CUTOVER_FLIP_TS` a global `settings_keys`
  constant), never scattered `os.getenv`.
- **Report-only / one-way-door discipline (CLAUDE.md adopt-with-a-kill-switch)** — the verified-restore
  proof *reports* (a red CI job + issue) before it can *gate* (Q2); the verify-boot is side-effect-free by
  construction (T-7 fix); `DECLARED_LOSS` requires an explicit **owner signature** on the M1 manifest,
  never a silent auto-drop — the same signed-disposition rail as SF-g and dossier 11's quarantine manifest.

---

## 8. Seam corrections (flagged; source-wins Q-0120)

1. **`StoreSpec`'s base field set is a CLOSED six at §2.8; `bears_value`/`rollback_class` are 09's
   *version-extension*, not §2.8 additions (corrects the earlier draft's misread).** Design-spec §2.8
   :866-869 declares **all six** base `StoreSpec` fields **together** — `table`, `sole_writer`,
   `retention`, `checkpoint_class` (`enum {ledger, aggregate, session}`), `invariant_tag`, and
   **`reader_domains`** (the earlier draft omitted this and wrongly narrated the six as "growing across
   §2.8/§5.3/§1560" — §5.3/§1561 only *reference* the fields in prose). `bears_value` is added by **spec
   09's version-extended `StoreSpec`** (`sb/spec/versioning.py`, `09` :79/:191) — an **unratified Gate-0
   proposal**, **not** dossier 11 (which only *mirrors* `bears_value` onto its `InvariantSpec`, 11 §2.1) and
   **not** the base §2.8 six. My `rollback_class` is a further **additive, compiler-derived** facet on
   **09's** version-extended `StoreSpec` (beside `bears_value`, because it *reads* `bears_value`) — never on
   the base six. Flagged so a builder homes it correctly and treats `bears_value` as a proposal that may be
   renamed/rejected at Gate-0 (RPO tiering §2.3 + derivation §2.4 re-bind if so). **No divergence — corrected
   provenance.**
2. **SF-g's `disposition` and my `rollback_class` are sibling axes, not the same field.** SF-g (vocab §⑧
   fork-8) disposes a store **dropped at migration** (`export`/`reverse-migrate`/`declared-loss` on
   `store_retirements.yml`); `rollback_class` disposes a **live** store's **writes stranded at rollback**.
   The two even *interlock*: a `store_retirements.yml` entry (SF-g `DROP`) is one of the `forward_map_kind`
   inputs that derives a store to `DECLARED_LOSS` (§2.4b). I deliberately **align the vocabulary**
   (`reverse_importable`≈`reverse-migrate`, `declared_loss`≈`declared-loss`) so the two read consistently,
   but they are **distinct axes** on distinct boundaries. Flagged so neither is mistaken for the other.
   **Consistent-with-skeleton, not a redefinition.**
3. **The `audit_log` is the *forensic* replay substrate, NOT a complete money replay log (corrects the
   earlier draft's "the replay log already exists").** The append-only `audit_log` (`07`, `mutation_id` PK,
   `prev_value`/`new_value`/`occurred_at`) is the post-cutover change record **for forensics + the
   `REPLAY_INTENT` list + a whole-window total** — but sibling **11 T-2** documents that value-bearing
   aggregate writes bypass the audited seam in the *legacy* bot (`set_coins`/`add_coins`, `economy.py:200-215`,
   no ledger/audit row), so it is **not** a complete money log. The new bot closes that hole *for
   post-cutover writes* via the **§③.4 `audit_completeness` fence** (every mutating ref routes through the
   audited seam) — the LEDGER-tier reverse-import depends on that fence. The **AGGREGATE-tier reverse-import
   reads the absolute value, not the log** (§2.4c), so it is robust to any audit gap. Flagged so a builder
   reuses the `audit_log` for forensics **and** knows the value guarantee is the per-store delta, not
   `audit_log` completeness. **A dependency + reuse note, not a conflict.**
4. **Rollback-topology section attribution + the `REVERSE_IMPORTABLE` grounding (cite corrections).** The
   "importer reads OLD → writes NEW; rollback re-deploys the old worker on the OLD DB" topology sentence is
   **§5.2 :1349-1351** (the closing paragraph of §5.2) — **not** §5.4; §5.4 :1367-1373 is the **5-step**
   sequence (step (4) `freeze → final import delta → flip`, step (5) the bounded rollback window). The
   earlier draft's §0 and T-4 mislabeled it §5.4/:1349-1351; corrected throughout. Relatedly, §5.2
   :1335-1336 guarantees **name-stability only** for `{subsystem_bindings, economy_audit_log, ai_review_log,
   ai_answer_presets}` — so `REVERSE_IMPORTABLE` is grounded on **forward-mapping invertibility** (§2.4b),
   not on "name-stable": `economy_audit_log` qualifies as `NAME_STABLE`, while XP/karma qualify only if
   their Q-0224 rename is an invertible bijection (`RENAME`), and fall to `DECLARED_LOSS` if it collapses.
   **Corrected grounding, not a redefinition.**
5. **`SB_VERIFY_BOOT` is a new *additive* operational `ConfigSpec` — flagged, not a vocab divergence.**
   Vocab ⑥ freezes `CONFIG_FIELDS` as "39 harvested + 8 new operational = 47 total, the ONE registry."
   The side-effect-free verify-boot (§2.2, the T-7 fix) needs one more operational field, `SB_VERIFY_BOOT`
   (`BOOL`, default `False`), consumed by the composition-root boot profile and gated to `SB_DATA_PLANE=test`.
   This **grows the operational-field inventory by one** (→ 48) exactly as sibling 09/11 grow the
   `ActorRef`/`IdempotencyKey` inventories — the grammar shape is unchanged; only the registry count grows.
   Flagged so a builder does **not** read the "47 total" as closed. **Additive, not divergent.**

*Written 2026-07-04 against the frozen shared vocabulary (`../shared-vocabulary.md`, all-five-pass),
the strand-2 siblings (`../strand-2-runtime-durability/07-workflow-engine.md`, `08-event-outbox.md`,
`09-scheduler-state.md`), and the strand-3 sibling (`11-data-integrity-repair.md`). Spot-verified
against shipped source / frozen siblings this session: `.github/workflows/backup-db.yml` (read in
full — `:23-26,31-37,56,61,119-124,131-139`), design-spec §2.8 (`:866-869`, all six base StoreSpec
fields together) / §5.2 (`:1315-1351`, topology sentence `:1349-1351`, name-stable set `:1335-1336`) /
§5.4 (`:1367-1381`, the 5-step shape) / the fake-HTTP harness (`:1431-1435`), `07` `audit_log` DDL
(`:408-422`, no `table`/`store` column), `08` `event_outbox` (§3.2), spec 09's version-extended
`StoreSpec` (`:79/:191`, `bears_value`), dossier 11 §2.1/§2.5/T-2, prod-deploy §Backups. **NOT SOURCE OF
TRUTH for runtime** — a Phase-B design contract for the strand-3 cross-cutting build to execute against.*
