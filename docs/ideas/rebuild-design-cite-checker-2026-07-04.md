# Idea — `check_doc_cites.py`: validate source citations in analysis/design docs

> **Status:** `ideas` — captured 2026-07-04 (Q-0089 session ender, foundational-design session).
> A small, disposable (Q-0105) doc-hygiene checker. Not yet planned; route through `/route-idea`
> when picked up.

## The problem it kills

Analysis and design docs cite shipped source by `path.py:NNN` constantly, and a **wrong cite
propagates silently**. The canonical case: audit A cited a `disbot/core/contracts.py:48-52`
`WorkflowResult` class that **does not exist** — the file is absent and the real analogue is
`services/lifecycle/contracts.py` + `StageResult` (final-judgment L-4 / L-25). That single fabricated
cite propagated into the design work-list and cost the 2026-07-04 foundational-design session real
cross-spec correction effort (a canonical source-wins grounding block had to be written into the
shared vocabulary and threaded through ~11 specs) before it was unwound.

The judgment already named the class ("structured-output validators should reject placeholder
strings", L-25) but only fabricated *cites* are the higher-frequency, higher-cost variant — and
they're mechanically checkable.

## The mechanic

A stdlib-only `scripts/check_doc_cites.py` (sibling to `check_docs.py`) that, over a target doc set
(default: `docs/analysis/**`, `docs/planning/rebuild-*`, `docs/analysis/rebuild-discovery/**/design/**`):

1. Extracts every `path:line` and `path:startLine-endLine` citation (regex over the doc text;
   restrict `path` to a repo-relative-looking form ending in a known source ext `.py/.ts/.tsx/.yml`).
2. Flags any cite whose **file does not exist** on disk (the fabricated-file class — the exact
   `core/contracts.py` bug).
3. Cheaply flags any cite whose **line number exceeds the file length** (the moved/renamed-line class).
4. (Optional, higher-value / higher-noise) records the cited line's text at authoring time so a later
   run can flag drift when the line's content changed — deferred; start with existence + line-bounds.

Output: a report grouped by doc, same shape as `check_docs`. `--strict` exits non-zero on any
missing-file cite (the unambiguous class); line-bounds warnings stay advisory until proven low-noise.

## Why it's worth having

- **Closes a real, recurring, expensive class at authoring time** rather than at
  read-time-across-N-specs.
- **Verifiable + disposable** (Q-0105): its output is checkable against ground truth in a few
  sessions; if it proves noisy, delete it.
- Pairs with `check_docs` and the source-wins rule (Q-0120) — it's the mechanical enforcement of
  "spot-verify load-bearing seams," applied to *every* cite, not just the load-bearing few.

## Bounds / non-goals

- Not a semantic checker — it verifies the *file/line exists*, not that the code *says what the doc
  claims*. (Claim-vs-source is what adversarial verifiers are for; this is the cheap floor under them.)
- Start narrow (missing-file → strict; line-bounds → advisory) to earn trust before widening scope.
- Bounded to source-path cites; prose references ("the resolver") are out of scope.

## Provenance

Surfaced by the 2026-07-04 foundational-design session (PR #1708), where the fabricated
`core/contracts.py:48-52` cite was the single most-threaded correction across the 14 design specs.
