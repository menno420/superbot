# Idea — a `check_reconciliation_consistency.py` guard for the four-homes summary

> **Status:** `ideas` — capture only. **Not a plan, not approval.** Session idea (2026-07-12, Q-0089,
> from the band-#2040 forty-fifth reconciliation pass). Workflow/tooling. Quick-win, disposable (Q-0105).

## The observation

Every Q-0107 reconciliation pass hand-writes the **same band summary into four homes**, each a
near-duplicate prose restatement with independent drift risk:

1. `docs/current-state.md` § **Last updated** header narrative (the per-pass `> Earlier:` block);
2. `docs/current-state.md` § **Recently shipped** grouped ledger entries + the **Last reconciliation
   pass: PR #N** marker;
3. `docs/current-state/S4-docs.md` § **Recently shipped (this sector)** pass bullet + the **▶ Next
   reconciliation due once merged PRs cross #M** line;
4. `docs/planning/reconciliation-pass-<date>-band<N>.md` the standalone pass record.

The *prose* is deliberately editorial (grouping + judgment) and should stay hand-authored — but the
**invariant facts embedded in that prose are not**: the **pass number** (44th → 45th), the **band
range** (#2012–#2040), the **marker value** (#2011 → #2040), and the **next-recon boundary** (#2070)
must be identical across all four homes. Today nothing checks that. A pass that updates three homes
and forgets the fourth (or fat-fingers `#2040` vs `#2070` in one place) ships silently — the exact
`#763`-style "a green checker that contradicts visible evidence" class, one level up.

## The proposal (a detector, not a generator)

A small stdlib `scripts/check_reconciliation_consistency.py` that **parses the four invariant facts
out of each of the four homes and fails if they disagree**:

- pass ordinal (`forty-fifth` / `45th`) consistent between the current-state header and the S4 bullet;
- band range + marker value consistent between the header, the Recently-shipped marker line, the S4
  bullet, and the newest `reconciliation-pass-*.md` record;
- next-recon boundary (`#2070`) == marker + 30, and identical in current-state marker + S4 `▶ Next`.

Deliberately a **detector, not a generator** — generating the editorial prose from a structured source
would lose the grouping judgment that makes the ledger readable (and the repo already prefers
"enforce, don't exhort", Q-0132). Warn-only first (Q-0105 unverified header), graduate to a
`code-quality` gate once it has proven itself over a few passes, same path the ledger/cadence checkers
took. Companion to the existing `reconcile-trigger-band-consistency-guard` and
`reconcile-headline-sector-currency-check` ideas — this one covers the *numeric* invariants those
two don't.

## Why it is worth having

The four-homes copy is the single most repetitive, most drift-prone chore of every pass (it recurs
~every day at burst velocity). A ~40-line detector converts "hope the human kept four prose blocks in
sync" into a CI fact — the friction→guard (Q-0194) shape the repo keeps reaching for. If it proves
noisy or low-value over a few passes, its Q-0105 kill-switch header says delete it.
