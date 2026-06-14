# Idea — media provider-outcome → persistent health finding (2026-06-14)

> **Status:** `ideas` (captured — not approved for implementation).
> **Lane:** media (YouTube) / health-diagnostics. **Size:** small.
> **Origin:** Q-0089 session idea, dropped while shipping content-free media diagnostics
> (PR #854).

## The gap

PR #854 added **process-local** provider-outcome counters
(`services/youtube_diagnostics.py`): success / key_missing / private_or_deleted /
**quota_limited** / **timeout** / fetch_error. They surface on `!platform media` and the
`youtube_provider_request_total{outcome}` Prometheus counter — but they **reset on every
restart**. A bot that exhausts its daily YouTube Data API quota at 14:00, gets restarted
at 15:00, and exhausts it again is invisible across the restart boundary: each boot shows
a fresh, small counter. The operator has no cross-restart signal that quota exhaustion (or
a sustained timeout rate) is a *recurring* problem rather than a one-off.

## The idea

Bridge the ephemeral counter into the **persistent operational-health findings store**
that P1-2 (#843, Q-0097) just made operator-manageable. When `quota_limited` or `timeout`
crosses a small threshold within a window, the media layer emits a **content-free** health
finding (`media.quota_exhausted` / `media.provider_unstable`) via
`health_findings_service` — fingerprinted, occurrence-counted across boots, and surfaced by
`!platform findings` with the existing resolve/ignore/reopen lifecycle. No new surface, no
content (the finding carries only the category + count), and it reuses the seam shipped
last session.

## Why it's worth having

- It is the natural **completion** of the diagnostics slice: counters answer "what's
  happening now?"; a finding answers "is this a recurring problem I should act on?".
- It is the **internal mirror** of how every other subsystem's recurring issues become
  visible (diagnostics → findings), so media stops being a blind spot.
- Small and decided-lane: the findings emit seam, the threshold pattern, and the
  content-free contract all already exist — this is wiring, not new architecture.

## Route

Decided lane (media + health-findings). Execute as a **small follow-up PR** once the
provider-execution hardening slice (the next queued P0-2 follow-up) lands — that slice will
likely add the timeout taxonomy this finding keys off, so sequencing it second avoids
re-touching the same code twice.
