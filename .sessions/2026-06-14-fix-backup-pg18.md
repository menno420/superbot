# Session: fix Postgres backup — pg_dump v18 client (server version mismatch)

> **Status:** `complete`

**Branch:** `claude/fix-backup-pg-version` · **PR:** #862 · **Date:** 2026-06-14 · **Type:** owner-directed ops bugfix (manual)

## What this session did
Live-verifying the backup (after the owner set `DATABASE_PUBLIC_URL`) drove a real production bug to
ground in two layers:
1. **URL was the template, not resolved** — diagnosed earlier; owner pasted the resolved URL (built
   via `railway_vars.py`, Q-0130). Connection then succeeded.
2. **pg_dump version mismatch** — Railway Postgres is **v18.3**; the workflow used the Ubuntu-default
   client **v16**, and pg_dump refuses to dump a newer server with an older client. Fixed in two parts:
   - install the **PGDG v18 client** (the default `apt postgresql-client` is v16 on Ubuntu 24.04);
   - **invoke pg_dump by explicit highest-version path** (`/usr/lib/postgresql/*/bin`), because the
     runner ships pg16 at `/usr/bin/pg_dump` which shadows the PGDG client on PATH.
   Both are future-proof: a newer client dumps older servers, and the path picks the highest installed.

Verified by dispatching the fixed workflow on this branch ref (not just trusting the change).
Also documented the version-mismatch failure mode in the workflow's failure-issue body.

## 💡 Session idea (Q-0089)
**Pin the backup runner's pg_dump to a known-good major via a tiny matrix var** (or assert
`pg_dump --version` major ≥ the server major before dumping, failing loud with a clear message) — so
a future Railway major bump produces a precise "bump the client" error instead of a silent empty dump.
Composes with the integrity guard already present. Ops lane; small.

## ⟲ Previous-session review (Q-0102)
Reviewing the **#859 sector-map/hook-policy session:** clean and well-scoped (settled Q-0137, built
the nav top layer, recorded Q-0139). **What it could improve:** it deferred the Hermes `skill-author`
meta-skill to "next session" without capturing a concrete *first step*; a deferred item with no next
action risks stalling. **System improvement:** when a session defers work, it should leave a one-line
"first concrete step" in the `.sessions` carry-forward so the next session starts mid-stride — which
this backup session benefited from (the prior backup diagnosis left an exact "paste resolved URL" step).

## Doc audit (Q-0104)
No `disbot/`/docs-content change (workflow-only fix). The fix was **verified live** on the branch ref,
not assumed — the strongest form of the Q-0104 "is it real?" check. `DATABASE_PUBLIC_URL` now set
(owner); the backup is the last red routine from the 06-14 control-plane audit going green.
