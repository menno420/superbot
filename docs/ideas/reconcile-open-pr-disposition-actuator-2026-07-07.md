# Idea: reconcile open-PR disposition actuator (guard → actuator)

> **Status:** `ideas` · captured by the band-#1800 reconciliation pass (2026-07-07) · Sector S4 ·
> Disposable (Q-0105).

## The friction (observed twice now)

The band-#1770 pass captured the
[codex/evidence-PR disposition *guard*](codex-evidence-pr-disposition-guard-2026-07-06.md) — a warn-only
checker that would *flag* an open evidence PR whose deliverable is already consumed into a merged doc. Good
signal. But a **flag is not a decision**: the same 5 Codex Gate-V evidence PRs (#1752–#1755/#1758) still sat
open through *two* passes (35th left them, 36th flagged-but-left them) before the band-#1800 pass finally
closed them by hand. The recurring cost isn't "not knowing they're stale" — it's that **each pass
re-derives the same merge-or-close judgment from scratch** and, under time pressure, defers.

## The actuator

Extend the proposed guard from *detect* to *propose-a-disposition*, as a `scripts/` dry-run helper the
reconciliation routine runs each pass:

- For every open PR, classify: `evidence-consumed` (added doc path/name referenced by a since-merged
  synthesis/corrections doc) · `superseded-ledger` (a docs PR whose content is now on `main`) ·
  `dep-bump` (dependabot — out of the docs lane) · `owner/in-flight` (recent human activity) · `unknown`.
- Emit a **ready-to-run disposition line** per PR: `close #N — evidence-consumed into <merged doc>` /
  `leave #N — dependabot runtime` / `review #N — unknown`, with the exact reason string.
- Stays **advisory + dry-run** (never closes anything itself — the reconciler still decides); it just turns
  the per-pass hand judgment into a pre-computed proposal so "defer again" stops being the path of least
  resistance. Disposable (Q-0105) if it proves noisy; low value once the verification-fleet stops minting
  raw evidence PRs.

## Why it's worth having

It closes the loop the band-#1770 guard-idea *opened*: detection without a proposed action is what let the
PRs rot a second pass. Same stdlib / advisory shape as the open-PR staleness classifier; it encodes the
Q-0125 "noting is not disposition — act on it" rule into the tooling instead of relying on each reconciler
to re-decide under pressure.
