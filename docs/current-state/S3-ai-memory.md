# S3 — AI-Memory system (the mechanism) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S3 · Map:
> [`../repo-sector-map.md`](../repo-sector-map.md).
>
> *The self-improving-agent engine — checkers, hooks, router, context tooling. Shippable on its
> own; distinct from S4 (the docs content it produces) and S5 (its operation).*

**Recently shipped (this sector):**
- **Per-claim / per-sector coordination-file restructure** (this PR, Q-0195) — `active-work.md` →
  one-file-per-claim (`scripts/check_lane_overlap.py` reads the directory; `check_stale_claims.py`
  GC) + `current-state.md` → per-sector files. Justified by `tools/sim/claim_layout_sim.py`.
- **Lane-overlap claim-scan** (#1223) and the **repo-consistency-linter** (back-button /
  edit-in-place rules, #1189) mechanisms.

**▶ Next startable:**
- **Consistency-linter AI-nav PR 1** (`needs-hermes-review`)
  ([plan](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)).
- **procedures→skills Batch 2**
  ([plan](../planning/procedures-to-skills-conversion-plan-2026-06-17.md)).
- The **bot self-test walker** eval harness (pairs with S1 P1-1) · the **Hermes bug-triage** write.

**Note:** most S3 runtime depth is `needs-hermes-review` (self-initiated mechanism work). A fresh
idea may be promoted idea→plan→build at any time (Q-0172) — flag self-initiated promotions on the
session-log `⚑ Self-initiated:` line.
