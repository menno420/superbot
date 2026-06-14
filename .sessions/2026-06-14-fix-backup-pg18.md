# Session: fix Postgres backup — pg_dump v18 client (server version mismatch)

> **Status:** `in-progress`

**Branch:** `claude/fix-backup-pg-version` · **PR:** TBD · **Date:** 2026-06-14 · **Type:** owner-directed ops bugfix (manual)

## What I'm about to do
Live-verifying the backup (owner set `DATABASE_PUBLIC_URL`) surfaced the real root cause: the URL is
now correct (connection succeeds), but `pg_dump` aborts on a **server/client version mismatch** —
Railway's Postgres is **v18.3**, the workflow installed the Ubuntu-default client **v16.14**, and
pg_dump refuses to dump a newer server with an older client. Fix `backup-db.yml` to install the
PGDG **v18+** client (newer client dumps older servers → future-proof). Verify by dispatching the
fixed workflow on this branch ref before merge.
