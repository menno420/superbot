# 2026-06-26 — Wire ▶ Next freshness guard into /session-close

> **Status:** `in-progress`
> **Run type:** routine · dispatch
> **Branch:** `claude/franklin-sessionclose-freshness`

## What I'm about to do
Second slice of this dispatch run. PR #1476 shipped `check_sector_next_freshness.py`
(a guard for ▶ Next pointers at SHIPPED plans) but **a guard nobody runs is useless** —
it had no invocation site, so a stale pointer could still sit unguarded between the
30-PR recon passes (the S3 pointer #1476 fixed had been live 3 days).

This slice operationalizes it: add it to the `/session-close` Step-4 quality gate +
a remediation note, so every session re-checks ▶ Next freshness on the way out. This is
option (a) — the "smaller, surer win" — from #1476's session idea. Skill/orientation
edit only (not CLAUDE.md / hooks / settings — those stay read-only to an autonomous run).
