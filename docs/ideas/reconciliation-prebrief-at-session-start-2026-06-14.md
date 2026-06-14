# Idea — a reconciliation pre-brief dropped at SessionStart

> **Status:** `ideas` — capture, **not** a plan, **not** approval. Source code and the binding
> contracts win over this file. Lane: workflow / orientation (first-class per CLAUDE.md —
> "improving the orientation/tooling for the next session is first-class work").
> **Raised:** 2026-06-14, band-#840 Q-0107 reconciliation pass.
> **Provenance/reliability:** an orientation convenience; verify it actually saves the derive
> step over a couple of passes before trusting it, and delete it if a reconciler finds it stale
> or wrong more than it helps.

## The friction (felt this session)

Every reconciliation pass re-derives the same thing **by hand** before it can write its §1
"merged since the last pass" list: take the `Last reconciliation pass: PR #N` marker, walk
`git log` for every merged PR since #N, read each merge subject, then grep `current-state.md`
for each number to learn whether it's *already in the ledger* (recorded by its own session) or
*genuinely new this band*. This session that was ~8 tool calls (`git log`, per-PR `git
log --grep`, per-number `grep current-state`) before any real reconciliation thinking started.
The band-#820 pass hit the same wall and filed
[`ledger-checker-print-pr-subjects`](./ledger-checker-print-pr-subjects-2026-06-14.md), which
solves *one half* (print the subject for a **missing** PR).

## The idea — deliver the whole computed band where the routine already looks first

The SessionStart hook (`scripts/claude_session_start.sh`) **already** computes the `Recon: DUE`
banner from the marker vs the latest PR. Extend it so that, **when a recon pass is due / the
session is the `reconcile` routine**, it also writes a `reconcile-prebrief.txt` (gitignored,
ephemeral) and prints a one-line pointer to it. The pre-brief contains, pre-computed:

1. **The band** — every merged PR in `(marker, HEAD]`, each line: `#NNN  [in-ledger|MISSING]
   <merge subject>` (the print-subjects idea, band-scoped and presence-annotated).
2. **Open PRs with state** — the `list_pull_requests` snapshot the Q-0125 disposition step needs
   (the band-#820 §6 "open-PR-with-state" shape), with author so owner-PRs are obvious.
3. **The ratchet delta** — current Recently-shipped count vs the ratchet, so the trim-the-oldest
   step is known up front (this session that was a separate after-the-fact `check_docs` surprise).

The routine then **reads one file** instead of re-deriving with ~10 tool calls — the same
"deliver the computed context at the place the agent already reads" principle behind the existing
SessionStart banner, applied to the reconciliation pass's specific needs.

## Why it's distinct from the existing ledger ideas

- `ledger-checker-print-pr-subjects` is a *checker output* change (one half: missing PRs).
- `ledger-checker-range-scope` is about the checker's *window*.
- This is an **orientation/delivery** change: package the band + open-PRs + ratchet-delta into the
  SessionStart artifact a reconciliation routine reads first. It *composes* the print-subjects
  idea rather than duplicating it (build that first, then this consumes it).

## Slice

Runtime-lane (`scripts/` + the hook), so **out of scope for a docs-only pass** — grooming-lane.
Smallest first slice: emit just item 1 (the presence-annotated band list) from the existing hook;
add items 2–3 once the print-subjects checker lands. Keep it stdlib-only and gitignored.
