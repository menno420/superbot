# Session — Executor run: Postgres backup posture (band slot 3)

> **Status:** `complete` — the first autonomous night-executor run (issue #768,
> 2026-06-13 01:20 UTC). Trigger: `executor-nightly.yml` cron. Band slot 3: the
> standing irreversible-loss risk.

## What this run built

**PR #769** — Postgres backup posture (band queue slot 3):

- **`.github/workflows/backup-db.yml`** — daily 02:00 UTC cron (+ `workflow_dispatch`).
  Installs postgresql-client, runs `pg_dump --no-owner --no-acl` against
  `DATABASE_PUBLIC_URL` (Railway external proxy), compresses with gzip, uploads as a
  90-day GitHub Actions artifact. Opens a bug issue on failure for persistent
  notification even without email alerts.
- **`scripts/backup_db.py`** — local/ad-hoc backup using the same flags. Prefers
  `DATABASE_PUBLIC_URL` (external) and falls back to `DATABASE_URL`. Prints a restore
  command at completion.
- **`docs/operations/production-deployment.md`** — Backups section filled in:
  automated posture, one-time owner setup (add `DATABASE_PUBLIC_URL` GitHub secret),
  restore procedure, and a note that Railway PiTR snapshots are a complement.

**Owner action required:** add `DATABASE_PUBLIC_URL` as a GitHub Actions secret
(Railway → Postgres → Connect → public proxy URL) before the first scheduled run
at 02:00 UTC produces an artifact.

## Phase gate + scope check

Phase gate reported `fix`. The backup posture is band slot 3 (planned-step execution) —
within scope. No runtime code touched; the PR qualifies for Q-0113 self-merge.

## ⚠️ Unconfirmed items carried from the previous session (#765)

The session log for #765 flagged three unconfirmed maintainer steps:
1. **Railway deploy of `CLAUDE_ROUTINE_*` vars** — not verifiable from here.
2. **Dispatch routine prompt version** (should carry the #761 free-form prompt) — not verifiable.
3. **Routine models** (dispatch/executor → Opus, reconciliation → Sonnet/Opus) — not verifiable.

These remain open. **Next human session should verify** the Railway deploy and the three
routine configs before assuming `/bugreport` + `/dispatch` are live.

## 💡 Session idea (Q-0089)

**Backup dump integrity check** — after `pg_dump` produces the `.sql.gz`, add a step to
`backup-db.yml` that verifies the dump contains a minimum number of `CREATE TABLE`
statements (e.g., `zcat dump.sql.gz | grep -c "^CREATE TABLE"` ≥ threshold). This catches
the silent-failure class where pg_dump exits 0 but produces an empty or truncated dump
(permission error, empty DB, wrong URL). Turns the backup posture from "we upload something"
to "we upload a verifiable schema snapshot." Small one-step addition; fits the Q-0105 posture
of confirming tooling output before trusting it.

Idea file: `docs/ideas/backup-integrity-check-2026-06-13.md`

## ⟲ Previous-session review (Q-0102)

Reviewing **#765 (autonomous loop live + Hermes dual-platform control plane)**:

**What it did well:** the scope was genuinely large (loop wiring + Hermes on two platforms)
and it shipped all of it in one session, with clear per-step PR granularity and thorough
documentation of the unconfirmed maintainer steps. The session also filed a clean
calibration checklist (Q-0105: watch the first autonomous runs) and was honest about
what it couldn't verify (Railway-side deploy). The BUG-0011 entry is thorough.

**What it missed / could have done better:** the session's own mid-run "ledger green ✓"
and "not due" signals were false (the regex bug) — it should have been more skeptical of
green-on-first-check, especially for a session that was actively merging PRs. The Q-0105
"confirm against ground truth" posture was invoked retroactively (by the #763 pass) rather
than proactively by the session itself. **System improvement:** before trusting any audit
checker's green signal on a session that merges many PRs, run a manual spot-check (e.g.,
`git log --oneline origin/main | head -20` vs. the ledger entries) rather than relying
on automation that has not yet been ground-truth-verified on that subject pattern.
