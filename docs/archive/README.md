# docs/archive — retired content (do not act on it)

> **Status:** `archive` — retired docs kept only for history. **Do not implement against
> these.** Start at `docs/current-state.md` for what is true now, and the subsystem folios
> for area state.

This folder holds superseded docs moved out of the live tree so the top level and
`docs/planning/` stay navigable. Everything here is a dated snapshot whose conclusions
were either shipped, replaced, or rolled into the living docs.

## Retired 2026-06 planning / audit burst

- `repo-cartography-2026-06-04.md` — early whole-repo cartography; superseded by the
  subsystem folios + `docs/repo-navigation-map.md`.
- `superbot-source-of-truth-index-2026-06-05.md` — an index router from the 2026-06-05
  burst; superseded by `docs/AGENT_ORIENTATION.md`.
- `superbot-next-session-roadmap-2026-06-05.md` — a point-in-time next-session roadmap.
- `superbot-architecture-priority-map-2026-06-05.md` — a point-in-time priority map.
- `stability-preimplementation-plan-2026-06-05.md` /
  `stability-implementation-plan-refined-2026-06-05.md` — stability plans; the stability
  work is the accepted `#535` baseline (`docs/current-state.md`).
- `cog-functionality-audit-2026-06-05.md` — a dated cog audit snapshot.

> Anything genuinely current was routed to `docs/current-state.md`, the folios, or the
> active trackers before these were archived. If you need a fact from here, verify it
> against source first.

## Related: in-place `historical` docs under `docs/planning/` and `docs/audits/`

Most retired plans/audits are **not** moved into this folder — they are rebadged `historical`
**in place** (so their inbound links stay intact) and indexed in the plan index
[`docs/planning/README.md`](../planning/README.md) (active vs. historical, by sector). That index is
the place to tell a live plan from a shipped/superseded one; the `> **Status:**` badge on each file is
the per-file signal. This `docs/archive/` folder holds only the physically-relocated early snapshots above.
