# Next-session brief — map the roadmaps/plans onto the 5 planning sectors

> **Status:** `plan` — a handoff brief for the next session (owner-requested, 2026-06-14). Now that
> the planning-sector top layer exists ([`../repo-sector-map.md`](../repo-sector-map.md), S1–S5), the
> roadmaps and plans should be *organised under those sectors*. This is the suggested next focus.

## Why
This session built the **top layer** of the 3-tap map — five planning sectors
(S1 Bot · S2 BTD6 · S3 AI-Memory system · S4 Documentation system · S5 Operations). But the existing
[`roadmap.md`](../roadmap.md) and the `docs/planning/` plans are still organised the *old* way
(by area/lane), not by sector. The map's value isn't realised until each plan hangs under its sector.

## The task (one focused session)
1. **Inventory** every live roadmap/plan: `docs/roadmap.md` horizons, the `docs/planning/*` plans,
   the `docs/planning/production-readiness/*` maps, and the open Q-router lanes.
2. **Assign each to exactly one sector** (S1–S5). Use the `repo-sector-map.md` test: mechanism vs.
   content for the S3/S4 split; BTD6 → S2 even though it spans runtime+data.
3. **Restructure `roadmap.md` by sector** — a Now/Next/Later horizon *per sector*, so each sector has
   a visible live queue (this also operationalises the Q-0137 "every sector has non-empty Now/Next"
   deep-clean terminal condition).
4. **Surface gaps:** which sectors have *no* live plan (likely **S4 Documentation system** and **S5
   Operations** — both under-planned today)? Note them for the owner.
5. **Reconcile the two taxonomies in-doc** — add the S→A (planning→review) mapping pointer in both
   `roadmap.md` and `repo-review-map.md` so they don't drift.

Scope: **docs-only**, modular, one session. Don't touch `disbot/`.

## The current standing next action (don't lose it)
Independent of the above, `current-state.md`'s standing next action is **P1-1 — the versioned
AI/BTD6 eval-smoke matrix** (gates · fallback · grounding-refusal). The #704 triage
([`../audits/pr704-live-test-triage-2026-06-14.md`](../audits/pr704-live-test-triage-2026-06-14.md))
surfaced a concrete P1-1 eval case: *the BTD6 capability message must match the actual refusal
behaviour, and asserted BTD6 numbers (Despo price, Elite Lych HP) must be grounded.* That work lives
in **S1 Bot product** (the in-bot AI slice) once sectors are mapped.

## Pointers for whoever picks this up
- The sector definitions + the planning-vs-review distinction: [`../repo-sector-map.md`](../repo-sector-map.md).
- The review taxonomy to reconcile against: [`../repo-review-map.md`](../repo-review-map.md).
- Open owner decisions still in flight: **Q-0137 Threads 1 & 2** (Hermes-dispatch-all-but-reconciliation
  + the staged deep-clean) — a sector-organised roadmap is a prerequisite for the deep-clean's
  per-sector terminal condition, so this task unblocks that.
