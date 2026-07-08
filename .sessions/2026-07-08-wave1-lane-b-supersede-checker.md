# Session — Wave-1 lane B: supersede-banner integrity checker

> **Status:** `in-progress`
> **Run type:** owner-directed campaign · EXECUTE lane (Wave-1 lane B)
> Branch: `claude/wave1-lane-b-supersede-checker`. Claim: `docs/owner/claims/claude-wave1-lane-b-supersede-checker.md`.

## What is about to happen

Ship the decided-lane, low-risk idea
[`docs/ideas/supersede-banner-integrity-checker-2026-07-06.md`](../docs/ideas/supersede-banner-integrity-checker-2026-07-06.md)
end-to-end: a new warn-first `scripts/check_supersede_integrity.py` (Q-0105 provenance header) that
verifies the supersede-banner handshake across `docs/` — (1) every `SUPERSEDED` banner names a successor
that exists, (2) the successor references the superseded doc back, (3) a superseded doc no longer carries
a live `plan` badge — plus unit tests, docs write-back (idea lifecycle → implemented, README index,
`current-state.md` ledger note). Docs/tooling only; no `disbot/` runtime changes.
