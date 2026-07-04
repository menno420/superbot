# Idea — reconcile-pass headline-sector currency check

> **Status:** `ideas` — captured by the band-#1680 Q-0107 reconciliation pass (2026-07-03).
> Lane: S3 (AI-Memory mechanism) / S4 tooling. Size: small, stdlib, disposable (Q-0105).

## The gap

The reconciliation routine reliably updates the **S4 docs sector file** (`current-state/S4-docs.md`)
every pass — it's the pass's home sector, so it's second nature. But the band's *content* usually
belongs to a **different** sector (S1/S2/S3), and that sector's live file (`current-state/SN-*.md`) is
the one a dispatcher reads to find the next startable item. Nothing checks that the headline-theme
sector file actually reflects the band it just reconciled.

Concrete miss this pass (band-#1680): the band was **dominated by the S3 rebuild arc** (capability audit
→ frozen BUILD-PLAN #1662…#1674, Phase-A conventions freeze #1679/#1680), yet `current-state/S3-ai-memory.md`
▶ Next still framed the rebuild as "Phase-2 design spec is DONE" with **no mention** of the capability
audit or Phase A — while S4-docs was fully current. The prior (32nd) pass had the same blind spot; it
was only caught here by hand because the theme was obvious.

## The proposal

A tiny advisory step/checker — `scripts/check_headline_sector_currency.py`, or a line in
`band_pr_status.py --themes` — that, given the band's grouped entries, infers the **dominant sector**
(the sector tag carrying the most / highest-numbered PRs) and asserts that sector's `current-state/SN-*.md`
**mentions at least one of the band's headline PR numbers**. If it doesn't, warn: *"band-#NNNN's headline
sector SN was not touched this pass — verify its ▶ Next is current."*

Output is advisory (exit 0), like the other reconcile-pass tools, so it never blocks. It turns the
"did I update the *right* sector file, not just S4?" judgment into a deterministic nudge.

## Why it's worth having

The per-sector split (Q-0195) made the sector files the dispatch surface, but the reconciler's muscle
memory is S4-centric — so the file a dispatcher actually reads for the hot lane is the one most likely
to lag. This is the sibling of the open-PR staleness classifier
([`reconcile-open-pr-staleness-classifier-2026-06-22.md`](reconcile-open-pr-staleness-classifier-2026-06-22.md)):
same shape (stdlib, read-only, advisory, disposable), same payoff (a drift-prone manual judgment becomes
a checked readout). Both are the "give the pass machine-help where the misses actually happen" pattern.

## House-style notes for the executor

- The grouped entries already carry sector tags in prose ("S3 rebuild —", "S1 fishing —"); parse those,
  or reuse whatever `band_pr_status.py` already extracts.
- "sector file mentions a headline PR" = grep the band's top PR numbers against `current-state/SN-*.md`.
- Mark it `unverified` per Q-0105: confirm the dominant-sector inference against a few real passes before
  trusting it; add the "delete this if it proves unreliable" header.
