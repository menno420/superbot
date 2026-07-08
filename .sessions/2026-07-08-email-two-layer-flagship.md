# 2026-07-08 — Email flagship: fold in the two-layer clear-path finding

> **Status:** `in-progress`

**Scope:** the clear-path test (coordinator PR #1839, merged) resolved the flagship's open half.
Fold the two-layer result into the Anthropic feedback email
(`docs/planning/projects-eap-activation-plan-2026-07-07.md` §4). Docs-only. Continuation of the
coordinator-kickoff thread (prior cards: `2026-07-08-email-compaction-verifiability.md`,
`2026-07-07-coordinator-kickoff-calibration.md`).

## What I'm about to do
- **Correct the now-inaccurate claim.** The email currently says destructive ops have "no
  self-clear path" and an unattended run "dead-ends with a present human as the only way through."
  The test refined that: the auto-mode **classifier** IS operator-clearable in-session (low bar —
  a generic "I give you explicit permission" answering a named request sufficed), but a **second**
  wall (the cloud environment's git credential) 403s the destructive push regardless, which no
  in-session grant clears.
- Rewrite the flagship as the **two-layer** finding (classifier: operator-clearable, coordinator
  not; credential: HTTP 403, unclearable in-session → no path to remote-ref deletion from a cloud
  session at all).
- Update the "what would fix it" to note **both layers must move together** (a pre-auth that
  clears the classifier still 403s unless the git credential carries matching scope).
- Meta-note: record that the flagship now reflects PR #1839's clear-path addendum.
- Aligned to the authoritative report addendum, not re-derived from the screenshot.
