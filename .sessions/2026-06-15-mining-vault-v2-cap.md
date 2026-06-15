# Session — Mining Vault v2: inventory soft-cap + vault-cap upgrade path

> **Status:** `in-progress`
> **Branch:** `claude/sharp-ptolemy-qf8jz6`
> **Started:** 2026-06-15 (autonomous routine — dispatched work order)

## What I'm about to do

A dispatched `CLASS: feature` work order arrived: **Mining Slice A — Vault v2**
(inventory soft-cap + vault-cap upgrade path), the next turn-key slice in
`docs/planning/mining-structures-skill-tree-plan-2026-06-14.md`.

The phase gate reads **FIX** (2 OPEN bugs + 28 not-done rows), but the gate
(Q-0114) gates only **agent-self-originated** features — and the owner
**directly corrected** this exact scenario in-session (2026-06-15, recorded in
`docs/ideas/dispatch-phase-gate-precheck-2026-06-15.md` ⚠ Correction): a
*dispatched* work order is **owner-directed** and flows freely, the same as a
bug fix. The prior run built mining Slice D (#891) on that correction. So this
run **builds** Slice A (gating it would repeat the mistake the owner called out).

Plan: pack soft-cap (distinct item-types, **warning only — never blocks**) +
an upgradeable vault capacity (coin sink) — all **additive**, honoring "warn at
cap, do not hard-block mining; no hard cap approved."

(Status flips to `complete` as the final step — Q-0133 born-red gate.)
