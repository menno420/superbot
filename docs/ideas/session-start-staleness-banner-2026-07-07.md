# SessionStart staleness banner — detect a behind-origin clone before it lies to you

> **Status:** `ideas` — captured 2026-07-07 (Q-0089 session idea, Projects-EAP eval-journal
> session). **Subsystem:** none (agent-workflow / session tooling).
> **Owner-gated half:** the SessionStart hook is executable config (Q-0106) — the hook change
> itself needs an owner-directed session or a router DISCUSS Q; the standalone checker script
> is free to ship.

## The incident that motivates it

The SuperBot Project coordinator's container clone was **7 merged PRs behind origin** at its
first turn (700bdce vs fe297a8) — the evaluation guidebook it was told to follow did not exist
on local disk and had to be fetched via the GitHub API. Trusting local disk would have produced
answers from a stale world (journal entry: `docs/planning/projects-eap-evaluation-log.md`,
2026-07-07 ~22:15Z). The same trap exists for any resumed/warm container: nothing in
`scripts/claude_session_start.sh` fetches or compares against `origin/main` today (verified by
grep, 2026-07-07).

## The idea

A tiny `scripts/check_clone_staleness.py` (or a few lines in the SessionStart hook, owner-gated):
`git fetch origin main` (timeboxed, failure-tolerant) → count `HEAD..origin/main` commits → if
N > 0, print a **loud banner**: `⚠ CLONE STALE: N commits behind origin/main — branch from
origin/main, not HEAD`. Sessions already branch from `origin/main` when told to; the banner
makes the failure mode visible when they aren't told to. Cheap, read-only, and converts the
coordinator's lived friction into an enforcing guard per Q-0194 ("friction → guard").
