# Subsystems — per-area documentation folios

> **Status:** `reference` (the folio convention) + a living index.
> Source code and `docs/current-state.md` win over anything here.

A **folio** is the single entry point for one part of the bot, so a session working
on that area reads *one* page instead of hunting across `docs/`. A good folio also
lets you spot adjacent work and **self-direct the next session** for that area.

## Folio template (the standard shape)

Each `docs/subsystems/<area>.md` should carry:

1. **What & where** — one-line scope + the key source dirs/files.
2. **Rules & approved structures** — the binding contracts for this area (link;
   don't restate) + any approved patterns.
3. **Current state** — what works / what's degraded *for this area* (links to
   `docs/current-state.md`).
4. **Plans / pending approval** — link to authoritative plans; do not duplicate them.
5. **Ideas (not approved)** — link to `docs/ideas/…` when one exists.
6. **Next candidates** — ranked, with enough context to self-direct the next session.
7. **Related docs** — the authoritative contracts, plans, and references.

**Drift-guard:** a folio's "Current state / Next candidates" is the area's *detail*
home; the global `docs/current-state.md` stays a *thin index* over them. One fact,
one home — vertically too.

## Subsystem index

| Subsystem | Folio | Key docs |
|---|---|---|
| AI | ✅ [`ai.md`](./ai.md) | (see folio) |
| Health / diagnostics | ✅ [`health-diagnostics.md`](./health-diagnostics.md) | (see folio) |
| Server management | ✅ [`server-management.md`](./server-management.md) | (see folio) |
| Settings / bindings / provisioning | ✅ [`settings-bindings-provisioning.md`](./settings-bindings-provisioning.md) | (see folio) |
| BTD6 data / tools | ✅ [`btd6.md`](./btd6.md) | (see folio) |
| Games | ✅ [`games.md`](./games.md) | (see folio) |
| Media / YouTube | ✅ [`media-youtube.md`](./media-youtube.md) | (see folio) |

> These folios intentionally link to existing contracts, ledgers, plans, and history.
> Move an underlying doc only when doing so reduces drift without obscuring authority or
> creating risky reference/doc-test churn.
