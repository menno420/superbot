# 2026-07-08 — Anthropic feedback email: compaction + verifiability audit

> **Status:** `complete`

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

## What shipped (PR #1838)
- **Compacted the email** ~20% and, more importantly, removed the two worst readability drags:
  the ~14-line auto-mode "wall" is now an 11-line flagship paragraph that points at the attached
  report instead of re-stating its table, and the duplicated "good moment" opening is merged into
  one. Findings tightened to ≤3 lines each; the flagship + fix are promoted above the smaller asks.
- **Verifiability audit — every surviving claim maps to evidence:** probe report (flagship, cell
  #4), committed in-repo artifact (cell #2 dispatch templates, WIP-gate #843, claim files),
  documented Claude Code behaviour (PR-webhook gap, 4 KiB cap), or an explicit "not yet tested"
  marker (cells #1, #3, kept honest). Dropped the one inferred/non-observed claim (the parenthetical
  that cloud has no prompting-mode switch and `.claude/settings.json` is classifier-overridable).
- **Corrected a factual claim:** "~1,800-merged-PR" → "~1,700" (GitHub search: 1,741 merged; the
  shared issue/PR counter at #1837 overstated it). Exactly the class of unverifiable claim the pass
  was meant to catch.
- **Repo-visibility check changed the attach guidance:** `superbot` is public → added the report's
  public URL inline in the draft (owner later confirmed all repos public, Project itself private/
  unshareable). Updated the meta-note accordingly.

## Follow-ups flagged to owner (not blocking this PR)
- Tests that would harden thin cells, most-sure-per-effort: (1) does explicit user-naming *clear*
  the destructive wall? — only the deny half is proven; (2) red-vs-broken side-by-side for the
  *sidebar* axis; (3) true Project-memory write-back (nothing committed); (4) a real dedupe
  collision; (5) measure the exact spawn-cap bytes. Each is a real run reported as-is, never staged.

## ⚑ Self-initiated
None beyond the owner-directed compaction/audit task.
