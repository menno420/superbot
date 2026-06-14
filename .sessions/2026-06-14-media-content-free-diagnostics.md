# Session — P0-2 follow-up: content-free media diagnostics

> **Status:** `in-progress`

**Branch:** `claude/p0-2-content-free-media-diagnostics-2026-06-14`
**Class:** correctness (P0-2 media/YouTube follow-up)

## What I'm about to do
Implement the P0-2 follow-up slice **content-free media diagnostics** for the
media/YouTube cache subsystem (readiness-map row "Media-specific
diagnostics/metrics/operator status" = *Not Done* → Done):

1. Docs-first: `docs/planning/p0-2-content-free-media-diagnostics-plan-2026-06-14.md`
   (scope + acceptance). This PR opens born-red.
2. Surface **bounded cache health metrics** (size/counts/age/expiry/last-purge
   status) + **provider-request outcome counters** (success/timeout/quota/error
   categories) — content-free: never re-reads or exposes raw provider payloads
   (no description/transcript/title/summary in any metric/log/snapshot).
3. New `!platform media` operator surface + a `media` runtime diagnostics
   provider; tests pinning no-raw-payload exposure.

Acceptance: `check_quality --full` green · `check_architecture --mode strict` 0
errors · no-raw-payload exposure tests pass.
