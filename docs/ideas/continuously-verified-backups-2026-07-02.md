# Continuously-verified backups — the restore drill as a scheduled workflow (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, owner-requested harvest). Not approved for
> implementation.

## The idea

Upgrade the Railway plan's one-shot **R6 restore drill** into standing CI: a scheduled (weekly or
monthly) `.github/workflows/restore-verify.yml` that spins up a Postgres **service container**,
downloads the newest `postgres-backup-*` artifact, restores it, and asserts substance — table
count ≥ the dump-integrity floor, row counts > 0 on load-bearing tables (`economy_audit_log`,
`subsystem_bindings`, `game_state`, settings), a spot value or two — then reports one line
(and opens an issue on failure, like the backup workflow itself).

## Why it's worth having

Today's audit made the pg_dump workflow the **only** backup layer (Railway volume backups proved
plan-gated on Hobby) — and its own header still says *"UNVERIFIED … run a test restore."* A backup
that has never restored is a hope; one that restored **once** decays silently (schema drift, a
pg_dump flag change, an extension the restore needs). Continuous verification converts "we have
backups" from a belief into a monitored fact — and it is the cheapest possible rehearsal of the
rebuild's importer discipline (§5.2's "verified against a snapshot fixture" is this same muscle).

## Route

S5 (operations) · free-to-ship CI lane (Q-0194); one workflow + a small assertion script. Supersedes
R6-as-one-shot in `../planning/railway-setup-plan-2026-07-02.md` §6 when built (the first green run
*is* the drill). Postgres major must match the server (18 — the workflow already documents the PGDG
pattern).
