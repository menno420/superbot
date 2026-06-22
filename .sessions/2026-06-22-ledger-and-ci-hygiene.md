# 2026-06-22 — ledger drift fix + design-system CI-coverage gap (post-botsite hygiene)

> **Status:** `in-progress` — born-red card (Q-0133). Flips to `complete` as the final step.
> Routine · dispatch ("Continue from where you left off" after PR #1305 + #1308 merged).

## Arc (what I'm about to do)

Both botsite slices this session merged (#1305 React foundation, #1308 contract guard). The
SessionStart hook flagged **real ledger drift** (Q-0166 fix-on-sight): **#1279 (reaction-roles
PR 6 — PIL banner cards)** merged but is *under* the reconciliation marker #1291, so it's a
genuine miss, not benign newest-merge lag → fix now. While fixing it I caught a **CI-coverage
gap I introduced in #1308**: the TS contract test (`data.test.ts`) reads
`botsite/data/site_data_contract.json`, but `design-system-ci.yml` is `paths`-filtered to
`design-system/**`, so a change to the contract (or the botsite producer) alone wouldn't re-run
the TS guard. This is a small, safe, docs+CI hygiene turn — no runtime code.

This PR:
1. **Ledger drift (#1279)** — record reaction-roles PR 6 as shipped in `current-state.md` (both
   reaction-roles bullets) + the S1 sector file; correct the stale "PR 6 … remains" prose so only
   the gated web builder (Surface A) is shown outstanding. `check_current_state_ledger --strict`
   green afterward.
2. **CI-coverage gap** — add `botsite/data/site_data_contract.json` + `botsite/site_data.py` to
   `design-system-ci.yml`'s push + PR `paths`, so a contract/producer change re-runs the
   cross-package TS guard (#1308's design↔data seam).
3. **Stale-claim GC** — delete my two merged-branch claim files (`s56i3y`, `s56i3y-2`) the
   `check_stale_claims` GC flagged.

## Shipped

_(filled at close)_

## Session enders

_(filled at close)_
