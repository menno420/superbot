# Idea — reconcile-pass open-PR staleness classifier

> **Status:** `ideas` — captured by the band-#1290 Q-0107 reconciliation pass (2026-06-22).
> Lane: S3 (AI-Memory mechanism) / S4 tooling. Size: small, stdlib, disposable (Q-0105).

## The gap

The reconciliation routine's **open-PR disposition step (Q-0125)** is the one part of the pass with **no
tooling assist**. The ledger half is now well-tooled — `band_pr_status.py --themes` drafts the grouped
entries and `trim_recently_shipped.py --apply` does the trim — but disposing open PRs is still a manual
read: `list_pull_requests` (state=open), then eyeball each one's age, labels, and CI to decide *active vs.
parked vs. stale*. The routine itself flags this as the easy-to-miss step: **#766 sat red for ~21h and #771
sat redundant**, unnoticed by two prior passes.

## The proposal

A small stdlib script — `scripts/check_open_pr_disposition.py` (or a `--open-prs` flag on
`band_pr_status.py`, which already talks to the GitHub REST API) — that fetches open PRs and **buckets**
them:

- **active in-flight** — pushed within the last ~24h, or a born-red `in-progress` session card present
  (don't touch — Q-0124);
- **parked carve-out** — labelled `needs-hermes-review` / `do-not-automerge` (leave for review);
- **genuinely stale** — no push in N days, no carve-out label, CI red or mergeable-conflict — **the only
  bucket the reconciler must actively dispose** (close-redundant / fix-red / flag).

Output is advisory (exit 0), like the other reconcile-pass tools, so it never blocks. The reconciler reads
the *stale* bucket and acts; the *active* and *parked* buckets are auto-explained, removing the per-PR
manual classification that's currently done by hand every pass.

## Why it's worth having

It closes the symmetry: the pass has machine help for **ledger** reconciliation but none for **open-PR**
reconciliation, which is exactly where the documented misses happened. It is the natural sibling of the
band-status classifier (#1181) and the trim actuator (#1206) — same shape (stdlib, read-only, advisory,
disposable), same payoff (turn a drift-prone manual chore into a deterministic readout the next run trusts).

## House-style notes for the executor

- Reuse the GitHub REST access pattern already in `band_pr_status.py` / `check_loop_health.py` (the
  `gh`-absent stdlib-REST fallback added in #1174), so it works in-container without `gh`.
- "born-red session card present" = the PR adds a `.sessions/*.md` with `> **Status:** \`in-progress\``;
  the gate logic already lives in `scripts/check_session_gate.py` — reuse, don't duplicate.
- Mark it `unverified` per Q-0105: confirm the buckets against a few real passes before trusting them; add
  the "delete this if it proves unreliable" header.
