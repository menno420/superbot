# 2026-07-08 — Anthropic feedback email: compaction + verifiability audit

> **Status:** `in-progress`

**Scope:** owner asked to (1) make the Anthropic Projects-EAP feedback email
(`docs/planning/projects-eap-activation-plan-2026-07-07.md` §4) more compact, and
(2) confirm every claim in it has a clear, verifiable test. Docs-only; no `disbot/` changes.
Continuation of the coordinator-kickoff thread (prior card:
`2026-07-07-coordinator-kickoff-calibration.md`, PR #1837 merged).

## What I'm about to do
- Audit each email claim against its evidence (probe report row / committed artifact /
  documented behaviour / honest "not yet tested" marker) and cut anything unverifiable.
- Correct "~1,800-merged-PR" → the real merged count (verified via GitHub search: **1,741**).
- Compact ~40%: let the attached probe report carry the action-by-action detail instead of
  re-stating it in-line; tighten each of the four findings to ~2 lines; drop the softest
  (inferred, not observed) parenthetical about cloud prompting-mode / settings.json override.
- Keep the honest "not yet stress-tested" markers on cells #1 (dedupe) and #3 (red-vs-broken).
