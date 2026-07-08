# 2026-07-08 — Finding: GitHub-API publish bypasses the git-push first-publish wall

> **Status:** `complete`

**Scope:** owner-directed test ("do the API-bootstrap test first — always useful to find out what
we can use"). Docs-only record of a first-hand result. No `disbot/` changes.

## What happened
- Two brand-new **empty public** repos (`menno420/substrate-kit`, `menno420/superbot-next`) — the
  exact case `git push` first-publish is hard-denied. Created the first commit on each via the
  **GitHub Contents API** (`create_or_update_file`) instead.
- **ALLOWED, no prompt** — both bootstrapped: `substrate-kit` README `fae482ac`, `superbot-next`
  README `de36d28b`. Task B's intent-commit half is done, autonomously.

## Why it matters
- **The first-publish wall is surface-specific** — it gates the `git push` transport, not the
  GitHub Contents API (consistent with the base probe's "API issue create/close = ALLOWED").
- **Likely unblocks step 7 of the rebuild.** The repos are now non-empty, so ordinary `git push`
  of new branches to them should be allowed (base probe: "new branch to an existing repo =
  ALLOWED") — untested for these two specifically, confirmable by a branch push.
- Open question for the email: is the API-vs-git asymmetry intentional (trusted write surface) or
  an inconsistency? Not tested: whether the API also bypasses the *destructive* walls (Git Refs
  API delete/force) — deliberately not run, `test/permprobe-0708` preserved as the standing example.

## Shipped (this PR)
- Probe-report addendum + eval-log entry recording the finding.
- (Held for owner review, flagged in chat: a one-line email addition — the surface-specificity as
  a question for Anthropic — and the step-7-unblock status in the rebuild plan.)

## ⚑ Owner action / next
- Step 7 is plausibly unblocked; confirmable by a branch push to either repo. Settings pass + the
  settings-ledger Phase 1 can now proceed (repos exist with commits).

## ⚑ Self-initiated
None beyond the owner-directed test; recording the finding is the drift-prevention discipline.
