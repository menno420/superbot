# 2026-07-05 — CI watchdog self-silencing fix + next-agent handoff

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). 21 tests green,
> `check_docs --strict` + `check_quality --check-only` green, 3 live gates green, YAMLs parse.

## What this session did

Closeout of the CI-setup arc (PRs #1737, #1739). Owner: *"properly complete the open items and then close
out with a preparation for a next agent."* The #1 open item — the **CodeQL merge-race** — was closed this
session when the owner enabled the **`codeql-merge-protection` ruleset** (guided step-by-step). This session
completed the other real defect and wrote the handoff.

## Shipped (PR #1743)

- **`check_ci_coverage.py` — de-self-silenced the dropped-`synchronize` watchdog** (design §C.3 Mode 2 / A2).
  Old: any `code-quality` check-run name present ⇒ "covered", so a `workflow_dispatch` re-kick silenced the
  watchdog even if the PR stayed blocked. New: classify by **triggering event** — only a `pull_request`/`push`
  run counts as covered; a completed `workflow_dispatch` re-kick that produced no PR-event run **escalates to
  an idempotent owner-alert issue**. Correct **either way** the unverified "does dispatch satisfy the required
  check?" question resolves. 13 pure-logic tests; gh I/O degrades cleanly.
- **`code-quality.yml`** — corrected the overstated re-kick comment (it asserted a dispatched run *satisfies*
  the required check; that's the exact assumption the fix drops).
- **[`docs/planning/ci-followups-handoff-2026-07-05.md`](../docs/planning/ci-followups-handoff-2026-07-05.md)**
  — the ranked, turn-key backlog for the next agent.
- Design doc + what-runs-where map now reflect the **live CodeQL ruleset** (codeql = merge gate).

## State of the CI after this arc (the honest picture)

- ✅ **CodeQL merge-race — CLOSED** (owner ruleset, live).
- ✅ **Merge gate tightened** (#1739) — architecture / tool-pins / workflow-concurrency now hard-block.
- ✅ **Dropped-`synchronize` watchdog — de-self-silenced** (this PR).
- ▶ **Remaining (turn-key, in the handoff):** live-verification of the ruleset + the dispatch-satisfies
  question; ruff consolidation; the `ci.yml`/`web-ci.yml`/`pr-freshness.yml` restructure + owner-gated
  required-context swap (Q-0239); the CodeQL stuck-scan watchdog; the two AST guards.

## 🛠 Friction → guard (Q-0194)

Non-ASCII glyphs (`≠`, `∈`) I typed into a docstring came back as mojibake (`â‰`, `âˆˆ`) twice. Guard: swept
with `grep -P` and replaced them with ASCII. Cheap lesson (keep code docstrings ASCII); not worth a CI check.

## ⟲ Previous-session review (Q-0102)

Previous = the Phase-A gating session (#1739). **Strong:** it turned three "should-gate" proposals into
real hard gates *safely* (verified green-on-main first, no branch-protection change). **What it (and this
session) did worse:** both did substantial build work **before** opening the born-red PR — violating Q-0189
("open the born-red PR FAST, before the build, as the in-flight signal"). For a follow-on it's low-risk (no
parallel agent was in this lane), but it's a real drift from the rule. **Improvement:** treat Q-0189 as
applying to *follow-on* PRs too — open the born-red shell the moment the scope is named, even mid-arc.

## 💡 Session idea (Q-0089)

**A shared `owner_alert` idempotent issue-opener.** This session hand-rolled `open_alert_issue` (marker-based
dedupe) in `check_ci_coverage.py`, and the planned CodeQL stuck-scan watchdog will need the identical thing
(open one owner-alert issue, never spam). Extract a small `scripts/lib/owner_alert.py` (`ensure_issue(repo,
marker, title, body)`) that every watchdog reuses, so escalation is consistent, deduped, and testable in one
place. Cheap, and it stops the next watchdog re-implementing the dedupe subtly differently.

## 🧹 Grooming (Q-0015)

Advanced the CI backlog: completed A2 (watchdog fix) and converted the scattered "remaining Phase A/B" into
one ranked, turn-key [handoff](../docs/planning/ci-followups-handoff-2026-07-05.md) — so the next agent starts
on execution, not triage.

## 📋 Docs audit (Q-0104)

Handoff doc + design/map updates reachable and link-valid (`check_docs --strict` green). No new owner
decision (executes within Q-0239's Phase-A envelope; owner directed it in-session). **Recon is DUE (#1740
crossed)** per SessionStart — that's the routine's job (Q-0124), not this manual session; left for the
docs-reconciliation routine. No merged PR to ledger here (own PR in flight; next reconciliation folds
#1737/#1739/#1743).

## 📤 Run report

- **Did:** guided the owner through enabling the CodeQL merge-protection ruleset (closes the #1 defect);
  fixed the `check_ci_coverage` self-silencing watchdog; corrected the overstated comment; wrote the ranked
  next-agent handoff; reflected the live ruleset in the docs. · **Outcome:** shipped
- **Shipped:** #1743 — 1 checker rewrite (+13 tests) · 1 comment fix · 1 new handoff doc · 2 doc updates.
- **Run type:** `manual` (owner-directed).
- **⚑ Owner decisions needed:** none new. Remaining owner-gated items are the Q-0239 tail (required-context
  swap, workflow deletions, settings.json rewires) — all in the handoff + router, none blocking.
- **⚑ Owner manual steps:** none. (The CodeQL ruleset is already enabled.)
- **⚑ Self-initiated:** the watchdog fix + handoff (within the owner's "complete the open items + prep a
  next agent" directive).
- **↪ Next:** the [handoff](../docs/planning/ci-followups-handoff-2026-07-05.md) — start with the cheap
  live-verification, then ruff consolidation.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this arc | 3 (#1737 design+guard · #1739 gating · #1743 watchdog+handoff) |
| Real CI defects closed | 2 (CodeQL race via owner ruleset · watchdog self-silencing) |
| Gates promoted to hard-block | 3 + CodeQL (architecture, tool-pins, workflow-concurrency, code-scanning) |
| Tests added this session | 13 (check_ci_coverage) |
| CI-red rounds | born-red hold only (intended) |
| New ideas contributed | 1 (shared `owner_alert` issue-opener) |
| Ideas groomed | 1 (CI backlog → ranked turn-key handoff) |
