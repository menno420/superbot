# Session: correct the DATABASE_PUBLIC_URL backup status (it's working)

> **Status:** `complete` — docs-only; born-red gate satisfied by this card.

**Branch:** `claude/sharp-ptolemy-5mzbvb` · **Date:** 2026-06-14 · **Type:** docs (ledger accuracy fix)

## What this session did

The owner pushed back on my "DB backup still failing" claim — correctly. I'd relied on the open
"Postgres backup failed" issues, which **don't auto-close on success**. The actual run history shows
the backup **succeeded at 17:41:49Z 2026-06-14** (workflow_dispatch) after the PR #862 pg18-client +
`DATABASE_PUBLIC_URL` fix; the earlier failures were #862's test iterations + a pre-fix scheduled run.
Closed the three stale failure-issues (#823/#860/#861) and corrected the control-plane state ledger
(`autonomous-routines.md` row 2 ⬜→✅ + the summary note) — the stale "still unset" status was the
source of my wrong advice, so fixing it prevents the next session repeating it. `check_docs --strict` ✓.

## 💡 Session idea (Q-0089)

`backup-db.yml` opens a failure-issue on each failed run but never **closes** it on a subsequent
success — so resolved problems linger as open issues and mislead (exactly what happened here). Idea:
add a tiny success-path step to the workflow that closes any open "Postgres backup failed" issues
(`gh issue list --search ... | gh issue close`) when a run succeeds, so the issue tracker reflects
live state. Captured pending a dedup-grep.

## ⟲ Previous-session review (Q-0102)

My own earlier turn this session asserted a failure from stale signal (open issues) instead of the
authoritative source (workflow run conclusions) — a verify-don't-assume miss I'd just been preaching
for Hermes (#869/#873). Lesson, now applied: for "is X working?" check the **run/outcome history**,
not derived artifacts like auto-created issues that have no auto-close. The control-plane ledger fix
+ the proposed auto-close step turn that one-off correction into a durable guard.
