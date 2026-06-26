# S3 — AI-Memory system (the mechanism) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S3 · Map:
> [`../repo-sector-map.md`](../repo-sector-map.md).
>
> *The self-improving-agent engine — checkers, hooks, router, context tooling. Shippable on its
> own; distinct from S4 (the docs content it produces) and S5 (its operation).*

**Recently shipped (this sector):**
- **Settle-once money-safety guard** (`check_consistency` **Rule 6**, warn-first, #1454) — pins the
  settle-once terminal pattern on game-state views (#1444) + blackjack PvP (#1445, shared mixin
  relocated to `utils/`) so a money-paying game can't double-settle without tripping a checker.
- **Cross-domain routing-disjointness guard** (#1470) — a registry-driven harness pinning the AI
  task-router invariant *"BTD6 keywords never collide with the distinctive Limbus tokens"* (routing ·
  token disjointness across every domain pair · priority total-order), so adding the next knowledge
  domain is a one-line registration.
- **Per-claim / per-sector coordination-file restructure** (Q-0195) — `active-work.md` →
  one-file-per-claim (`scripts/check_lane_overlap.py` reads the directory; `check_stale_claims.py`
  GC) + `current-state.md` → per-sector files. Justified by `tools/sim/claim_layout_sim.py`.
- **Lane-overlap claim-scan** (#1223) and the **repo-consistency-linter** (back-button /
  edit-in-place rules, #1189) mechanisms; the linter's **`edit_in_place` rule graduated
  warn→error** (#1375) once the `views/ai/` in-place-nav migration cleared its last findings
  ([plan, now historical](../planning/ai-panel-inplace-navigation-plan-2026-06-19.md)).

**▶ Next startable:**
- **procedures→skills Batch 2**
  ([plan](../planning/procedures-to-skills-conversion-plan-2026-06-17.md)).
- The **bot self-test walker** eval harness (pairs with S1 P1-1) · the **Hermes bug-triage** write.

**Note:** S3 runtime depth is self-initiated mechanism work; the old `needs-hermes-review` review gate
is **retired** (Q-0197) — every PR now auto-merges on green CI. A fresh idea may be promoted
idea→plan→build at any time (Q-0172) — flag self-initiated promotions on the session-log
`⚑ Self-initiated:` line.
