# Idea — reject placeholder values in fleet structured outputs (workflow-layer guard)

> **Status:** `ideas` — capture only. **Subsystem:** none (agent-workflow tooling).
> **Provenance:** Fable-5 final-judgment session 2026-07-03 (PR #1701, Q-0089 session idea).

## The idea

Two independent multi-agent audits shipped **placeholder junk inside otherwise-validated
structured output** on the same day: audit A's ledger row 221 carries an adversarial verdict whose
`verdict_reason` is the literal string `"test"` (self-flagged as degenerate), and audit B's §8
contains **three literal placeholder rows** (`t/e/f` in title/evidence/fix cells — one of them
ranked HIGH). JSON-schema validation passed in every case, because a placeholder string *is* a
valid string.

Add a cheap **semantic placeholder guard** at the workflow/structured-output layer: reject (and
retry the agent once) when a required string field matches a placeholder shape — `test`, `t`,
`e/f`, `TODO`, `TBD`, `...`, `n/a` in a field whose schema description demands evidence/reasoning,
or any required field shorter than a per-field minimum. The schema layer already retries on
type mismatch; this extends the same retry loop to the degenerate-content class that actually
slipped through twice in production use.

**Why it's worth having:** the whole verification-fleet strategy (Q-0234 Gate-V, Q-0236 audits)
rests on structured agent outputs being trustworthy at scale; the failure mode is silent (a
placeholder verdict reads as a completed verify), was caught only by the capstone judgment pass,
and the fix is a few lines at exactly one seam. Evidence:
`final-judgment-fable5-2026-07-03.md` §2 row L-25.
