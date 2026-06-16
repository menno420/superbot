# Idea — the ledger guard should exempt self-referential reconciliation PRs

> **Status:** `ideas` — ✅ **SHIPPED 2026-06-16 (Q-0152)**: implemented in `find_missing` as a
> `reconcil`-in-merge-subject exemption (`_is_reconciliation_subject`). The diff-confinement bound
> below was deferred as merge-strategy-fragile; subject-match is tight enough + disposable (Q-0105).
> Kept for provenance. Routing: **S5 Operations / docs system**. Raised 2026-06-16 (Q-0089) by the
> diagnostic-mixin dispatch session (#943), from the recurring ledger drift it had to fix that run.

## The recurring drift (now observed at least twice)

`scripts/check_current_state_ledger.py --strict` flags every recently-merged PR that is missing
from `current-state.md` § Recently shipped. That guard does its job for real feature/fix PRs. But
a **ledger-reconciliation PR** (`docs(current-state): reconcile ledger …`) hits a structural
chicken-and-egg: its whole diff *is* the ledger, yet it **cannot list its own number** — the PR
number doesn't exist until the PR is opened, and the body is written before that. So a
reconciliation PR systematically omits itself, the guard flags it on the *next* session, and that
session burns a few steps adding the entry + archiving the oldest to hold the ratchet.

- #942 (this drift) reconciled #932–#936/#939 but not itself → flagged this session, fixed in #943.
- The same shape recurs every reconciliation pass; the band-#930 pass note already shows the
  manual "added X, archived Y to hold the ratchet" bookkeeping each time.

It self-heals within one session, so it is low-harm — but it is *guaranteed* recurring busywork,
which is exactly the drift class the loop is supposed to remove structurally rather than re-fix by
hand each pass.

## The idea

Teach `check_current_state_ledger.py` to **skip a PR that is pure ledger bookkeeping** — detect by
(a) title matching `^docs\(current-state\): reconcile ledger` (or a `reconcile`/`ledger` label) AND
(b) a docs-only diff touching only `docs/current-state*.md`. Such a PR ships no
feature/fix/runtime change a reader needs in the ledger, and structurally can't reference itself, so
the guard should treat its absence as expected, not drift.

Bound it tightly so it can't hide real work: the exemption applies **only** when the diff is
confined to the two current-state ledger files. A reconciliation PR that also touches runtime/docs
elsewhere is not exempt.

## Why it's worth having

It removes a recurring manual step from every reconciliation pass (the loop's own job is to kill
drift, and this is drift the loop generates and then re-fixes). Small, disposable (Q-0105 —
delete the exemption if it ever masks a real omission), and it closes the recurrence at the guard
level instead of relying on each next session to notice and reconcile.

## Dedup

Distinct from the living-ledger guard itself (which this *refines*) and from
`control-plane-single-source-pointer-2026-06-15` (which removed a *different* duplicated fact). No
existing idea covers the reconciliation-PR self-omission case.

## Gate

None — pure tooling, reversible. A future session that touches `check_current_state_ledger.py` can
add the title/diff exemption directly; until then the next session keeps absorbing the entry by hand
(as #943 did for #942).
