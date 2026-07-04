# Idea — ledger-fragmentation linter (consolidate same-arc Recently-shipped bullets)

> **Status:** `ideas` — captured 2026-07-04 (thirty-fourth Q-0107 reconciliation pass, Q-0089).
> Workflow/tooling idea for the docs-memory system (S4). Disposable per Q-0105.

## The friction (why)

The `current-state.md` § Recently-shipped ledger is soft-ratcheted at 20 and relies on the
**grouped-entry convention** — a band's closely-related PRs collapse into one bullet (e.g.
`#1662 · #1663 · … (S3 rebuild — capability audit)`) so the living ledger stays scannable. But a
*session* that opens its PR born-green and lands during a band adds its **own** individual bullet,
and several sibling sessions in one decision arc each do the same. This band's #1683–#1688 were six
separate bullets for **one** Phase-A conventions/hub/rubric decision arc — exactly the fragmentation
the grouped-entry convention exists to prevent. The trim actuator counts bullets but is blind to the
*relatedness* of adjacent ones, so the fragmentation survives every pass unless a reconciler notices
it by eye (this pass's Q-0102 review flagged it; nothing enforced it).

## The idea (what)

A **warn-only** linter (in `check_docs.py`, or a small `scripts/check_ledger_fragmentation.py`
disposable) that scans the Recently-shipped bullets and flags a run of **N ≥ 3 consecutive** bullets
that share a strong relatedness signal:

- the same **session branch** (parseable from the PR merge metadata) or same-day date stamp, **and**
- the same **theme tag** (the leading `(YYYY-MM-DD, <sector> — <theme>)` prefix) or overlapping
  **Q-number arc**.

When it fires, it prints: *"Bullets #A–#B look like one arc — consider consolidating into a grouped
entry before the next trim."* It never fails CI (same posture as the `--drift` dashboard reporter);
the reconciliation routine reads the warning and does the consolidation as part of the pass.

## Why it's worth having

- It **mechanizes the grouped-entry convention** the ledger already depends on — turning a
  "reconciler notices by eye" into an enforced-on-sight signal (Q-0194 friction → guard;
  "enforce, don't exhort").
- It keeps the living ledger lean *at the source*, reducing how often the 20-ratchet pushes still-recent
  band work into the archive just because it arrived fragmented.
- It is cheap, stdlib-only, read-only, and disposable — deleted if it proves noisy over a few passes.

## Scope / caveats

- `check_docs`/`current-state.md` are docs-tooling → **free to ship** (not owner-gated). Wiring it
  into the `code-quality` required check would be a CI change (leave warn-only / dispatch-run first,
  prove it against a few passes per Q-0105 before any hard gate).
- Relatedness heuristics need tuning — start conservative (require both branch-or-date **and**
  theme-prefix match) to avoid flagging genuinely distinct same-day bullets.
