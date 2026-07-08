# 2026-07-08 — Campaign self-audit (EAP probe: coordinator memory vs ground truth)

> **Status:** `complete`

**About to do:** Owner-directed EAP probe. Grade the coordinator's memory snapshot of the
Waves 1–3 coordination campaign (PRs #1844 #1845 #1846 #1850 #1851 #1854 #1855) against
git ground truth. Deliverable: `docs/eap/campaign-self-audit-2026-07-08.md` (roster graded
vs git, causality verified, per-session compliance, memory-depth probe, 7 EAP axis scores)
plus friction entries appended to `docs/planning/projects-eap-evaluation-log.md`.
Integrity rule: git wins every disagreement; discrepancies are the findings.

## What shipped (PR #1859)

- **`docs/eap/campaign-self-audit-2026-07-08.md`** — the full audit. Headline: coordinator
  same-day recall graded **≈0.98 precision / ~1.0 event-level recall** (52/53 checkable claims
  confirmed; the single contradiction — "16 unit tests" vs 15 shipped — was inherited verbatim
  from the W1-B worker's own card, not confabulated). Causality chain 4/4 supported from merged
  artifact contents. Per-session compliance 7/7 on claim-first / born-red / enders; one
  deviation (post-flip substantive commit `0dc13f6` on #1846); one record-vs-reality find (W3
  card says scratch branch "deleted"; it survives — the documented 403). Axis scores:
  use-case fit partial · judgment pass · reliability pass · memory pass (same-day scope only) ·
  proactivity pass · scheduling fail · sidebar states fail (thin, n=1).
- **`docs/planning/projects-eap-evaluation-log.md`** — six new entries: friction (a)–(e)
  (claims blind window · `list_pull_requests` token blowout · CI-churn merge latency with
  git-verified 22min–2h28m spread · bash GitHub-API proxy 403 → MCP-only polling · background
  children don't wake their parent worker) + one memory *win* entry for the probe itself.
- Method note: squash-merged PRs (#1845/#1850/#1851) have no branch commits reachable from
  main and auto-deleted branches, so their commit ordering was attested via the PR API and
  marked "(api)" in the compliance table — verifiability ceilings stated, never papered over.

## Verification

- `check_docs.py --strict` ✓ (badge fixed `report`→`audit` — `report` isn't a valid token)
- `check_plan_homing.py --strict` ✓ (81/81) · `check_supersede_integrity.py` ✓ (0 findings)
- `check_current_state_ledger.py --strict` ✓ exit 0 (24 PRs of benign newest-merge lag above
  marker #1830 — the Q-0166 exception; recon routine's job)

## ⚑ Self-initiated

- Added the sixth eval-log entry (the memory-win observation) beyond the dispatched five
  friction items — the log's integrity rule says log both directions, and the probe's headline
  result is a win, not a friction.
- Friction entry (c) ships with git-verified latency numbers that correct the coordinator's
  in-flight ~25-min estimate (typical case right, tail ~5× worse) — git-wins applied to the
  probe's own inputs.

## 💡 Session idea (Q-0089)

**Worker-report count verification as a session-close micro-check.** The probe's only
contradiction (15 vs 16 tests) was a worker miscounting its own shipped artifact, then the
count propagating card → PR body → coordinator memory unchallenged. Cheap fix shape: the
session-close skill greps `def test_` in any test file the session added and compares against
any number the card states (or simply appends the machine count to the card), so self-reported
counts are machine-anchored at the source. Dedup-checked `docs/ideas/` + roadmap: the
warn-first proving-period evidence-trail flag (#1854 card) records *checker runs*, not
self-reported artifact counts; no existing idea covers report-count anchoring. Card-flag
capture; worth an idea file if a second miscount class shows up.

## ⟲ Previous-session review (Q-0102)

Previous session (`2026-07-08-eap-email-agent-narrative.md`, PR #1858) did the reshape cleanly
and its "⚑ Open for the owner" list was exactly right — including flagging that the email's
`docs/eap/` self-audit link was still a forward reference. This session makes that link real,
which validates the flag. One concrete improvement it surfaces: a forward reference to a
not-yet-existing path is exactly the phantom-successor drift class
`check_supersede_integrity.py` catches for banners — a tiny `check_docs` soft-check for links
to non-existent `docs/` paths (dangling forward references, distinct from broken relative
links it already checks) would have tracked that email link mechanically instead of via a
card note. If `check_docs` already covers it for relative links, extend to backtick-quoted
path mentions — the form the email used.

## Docs audit (Q-0104)

Both strict checkers green (above). The audit doc is reachable via the eval log's memory
entry (and §6 links back); no new owner decision made — the probe was owner-specified, so
nothing to route to the question router. Nothing chat-only left unhomed: snapshot text,
grades, and friction all live in the audit doc + eval log. Claim file deleted at close.
