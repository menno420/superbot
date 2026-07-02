# S3 — AI-Memory system (the mechanism) · live state

> **Status:** `living-ledger` — per-sector live snapshot (Q-0195).

> Per-sector snapshot (Q-0195). Hub: [`../current-state.md`](../current-state.md) ·
> Forward queue: [`../roadmap.md`](../roadmap.md) § S3 · Map:
> [`../repo-sector-map.md`](../repo-sector-map.md).
>
> *The self-improving-agent engine — checkers, hooks, router, context tooling. Shippable on its
> own; distinct from S4 (the docs content it produces) and S5 (its operation).*

**Recently shipped (this sector):**
- **Reconcile-marker band-consistency guard** (`scripts/check_reconcile_marker.py`, warn-first,
  dispatch run 2026-06-27) — asserts the `Last reconciliation pass` marker in `current-state.md` is
  internally consistent (leading `PR #N` == the stated reset target · `band-#M` == `(N // 30) * 30` ·
  the linked pass-record doc exists); caught + fixed the live band-#1470 drift (marker read `#1472`,
  the pass's own PR, vs the reset target `#1470`). Idea `reconcile-trigger-band-consistency-guard`.
- **`check_ledger_hygiene` de-staled for the Q-0195 per-claim-file layout** (dispatch run 2026-06-27) —
  the retired shared `active-work.md` claim ledger left the linter's Active-claims scan no-op'ing
  against a pointer stub; repointed to scan `docs/owner/claims/*.md` and flag a `claude/<branch>`
  claimed by >1 file.
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
*(offline-fit tags — `[offline]` self-mergeable now · `[needs-live-bot]` needs a running bot / runtime
creds · `[owner]` needs an owner decision/action; see [`../repo-sector-map.md`](../repo-sector-map.md)
§ "the offline-fit startability tag".)*
- `[owner]` **🔒 THE REBUILD OWNER GATE — the Phase-2 design spec is DONE and the evidence package
  is IN** (2026-07-02): [`rebuild-design-spec-2026-07-02.md`](../planning/rebuild-design-spec-2026-07-02.md)
  (Fable-5 judge panel + Opus/GPT adversarial review), now backed by
  [`rebuild-linchpin-validation-2026-07-02.md`](../planning/rebuild-linchpin-validation-2026-07-02.md)
  (#1639) — **both previously-unproven linchpins built + measured**: the Phase-0.5 golden harness
  (`parity/` — replay-deterministic, coverage in `parity/COVERAGE.md`) and the grammar spike
  (tier-1/2 fit 73% as-specced → 85% with six named amendments; verdict **GO with amendments**).
  The owner ratifies the design + the backward-compat contract + the rebuild go/no-go (§10.2 lists
  exactly what approval means); **no Phase-3 new-repo code until then.** `[offline]` remaining
  ungated phases: Phase 0 (substrate-kit adaptive half) · Phase-0.5 telemetry sidecar capture ·
  Phase 1 (harvest) · Phase 2.5 (cold-start proof) — see the
  [strategy §3](../planning/fresh-rebuild-strategy-2026-07-02.md).
- `[offline]` **▶ FINALIZE THE MEMORY SUBSTRATE (owner-queued 2026-07-02, next up):** the owner will
  start a **Fable 5 ultracode** session to make the substrate-kit finished + shippable for a fresh
  repo. **The canonical startup prompt is
  [`rebuild-ultracode-handoff-2026-07-02.md`](../planning/rebuild-ultracode-handoff-2026-07-02.md)
  §5.B** (owner-elevated: the real new-repo gate), extended 2026-07-02 with the
  **context-economy engine** scope
  ([retention plan §10](../planning/memory-retention-and-context-economy-plan-2026-07-02.md), posture
  + inbox + shrink + ledger-depth decided in **Q-0214**) and a flagged-uncertainty list. Subsumes the
  old "PR 2 remainder + PR 3" framing of
  [the extraction plan](../planning/portable-substrate-kit-extraction-2026-06-13.md) (owner-re-elevated
  to top focus by the 2026-06-30 fresh-rebuild vision, #1589/#1590, reversing the band-#870 §6
  demotion). `[owner]` the final *extract to a standalone repo* step + the full rebuild go/no-go stay
  owner-driven.
- `[offline]` **procedures→skills Batch 2**
  ([plan](../planning/procedures-to-skills-conversion-plan-2026-06-17.md)).
- `[offline]` The **bot self-test walker** eval harness (pairs with S1 P1-1) — the harness scaffold is
  offline-buildable; `[owner]` the **Hermes bug-triage** write side stays gated on the VPS write scope
  (Q-0121).

**Note:** S3 runtime depth is self-initiated mechanism work; the old `needs-hermes-review` review gate
is **retired** (Q-0197) — every PR now auto-merges on green CI. A fresh idea may be promoted
idea→plan→build at any time (Q-0172) — flag self-initiated promotions on the session-log
`⚑ Self-initiated:` line.
