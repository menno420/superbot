# 2026-07-08 — Email flagship: fold in the two-layer clear-path finding

> **Status:** `complete`

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

## What shipped (PR #1840)
- **Flagship rewritten as the two-layer finding.** Layer 1 (auto-mode classifier): operator-clearable
  in-session at a low bar; coordinator-relay is not. Layer 2 (cloud environment's git credential):
  destructive push 403s regardless, unclearable in-session → no path from a cloud session to
  remote-ref deletion, operator present or not. Corrects the prior "no self-clear path / present human
  the only way through" (the human clears layer 1; layer 2 still stops it).
- **Fix section** now notes both layers must move together — pre-auth clears the classifier, but the
  op still 403s unless the git credential carries matching scope.
- **Meta-note** records the flagship reflects PR #1839's clear-path addendum.
- Aligned verbatim to the report addendum + eval-log entry the coordinator merged (#1839).

## ⚑ Live corroboration (worth noting)
This PR could not force-push the post-squash branch — auto mode denied `git push --force-with-lease`
with `[Git Destructive]` ("the user never named this force-push and its target"). So it ships from a
**fresh branch** (`claude/eap-email-two-layer-flagship`). The force-push wall the email describes hit
this very session — a first-hand instance, not a relayed one.

## ⚑ Owner action (unchanged from #1839)
`test/permprobe-0708` still exists and still needs a human with full git rights to delete (the
in-session grant cleared the classifier but 403'd at the credential layer). Owner can delete it via the
GitHub Branches UI whenever.

## ⚑ Self-initiated
None — owner/coordinator-directed correction (the #1839 card's "↪ Next" explicitly routes this fold-in).

## 💡 Session idea (Q-0089)
**Ship the email's flagship as a standalone "auto-mode capability + clearance" one-pager** (rows =
operation, cols = gating layer + what clears it), reusing the coordinator's #1839 capability-matrix
idea — so the *email* can link a crisp table instead of prose, and the same doc seeds substrate-kit's
environment-capability template. Dedup: extends #1839's idea toward the email artifact specifically.
