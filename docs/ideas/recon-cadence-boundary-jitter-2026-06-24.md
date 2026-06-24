# Idea — reconciliation cadence-boundary jitter guard

> **Status:** `ideas`. **Not a plan, not approval.** A capture doc so the idea lives in the repo,
> not in chat. Source code + binding contracts + `docs/current-state.md` win over anything here.
>
> **Subsystem:** none — agent-workflow / docs-reconciliation meta.

## The observation (band-#1410 Q-0089)

The band-#1410 reconciliation pass (2026-06-24) fired **~50 minutes** after the band-#1380 pass, on a
band of just **4 merges** — one of which (#1407) was the previous pass itself, leaving 3 product PRs
(the ticket subsystem #1405/#1410 + one BTD6 PR #1408). It fired because the previous pass reset its
marker to **#1404** while #1405–#1410 were already merged or in flight, so the very next merge crossed
the #1410 cadence boundary (every 30th PR, Q-0134) almost immediately.

The cadence is doing exactly what it's specified to do. But at **burst velocity** (dozens of merges a
day), a strict "every 30th PR" boundary can fire a **near-empty full-ritual pass right behind a full
one** — the ledger trim, the scorecard, the §4 queue re-plan, the idea/review enders — for a band too
small to warrant the ceremony. It's cheap, but it's not free (a whole self-merging PR + CI run), and
the §2 scorecard for such a band is necessarily "0/12 planned slices executed" noise.

## The idea

Add a **jitter guard** to the trigger path so a tiny band gets *folded into the next real one* instead
of spending its own pass:

- In `scripts/check_reconciliation_due.py` (and/or `.github/workflows/reconciliation-trigger.yml`),
  before opening a new `reconcile` issue, check whether the **previous pass** is too recent to justify
  another: suppress when *both* (a) fewer than **K product PRs** (e.g. K=8 — excluding the previous
  pass PR + trigger issues) have merged since the last marker reset, **and** (b) the last pass landed
  within the last **N PRs / M hours**.
- When suppressed, **record the skipped boundary** (a one-line note in `current-state.md` or a marker
  field) so nothing is lost — the next genuine pass reconciles the folded-in PRs and notes it absorbed
  the skipped boundary.
- Keep a hard ceiling so it can never suppress indefinitely (e.g. never skip two boundaries in a row,
  or never let > 1 full cadence accumulate unreconciled).

## Why it's worth having

- Removes the "near-empty pass right behind a full one" waste class this pass is itself an instance of.
- Keeps the *band scorecard meaningful*: every pass would score against a band large enough to have
  consumed some of the forward queue, so the planned-slice hit-rate metric (band-#1380 idea) measures
  signal, not 0/12 noise.
- Pure stdlib, advisory, reversible — fits the disposable-guard convention (Q-0105). If it ever
  suppresses a pass that should have run, the ceiling + skipped-boundary record make it self-healing.

## Relation to existing ideas

Complements the **planned-slice hit-rate tracker** (band-#1380) — that measures whether the queue is
predictive; this ensures each measured band is big enough for the measurement to mean anything. Both
are docs-reconciliation-loop tooling (S4/S3).
